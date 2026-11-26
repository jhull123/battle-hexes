"""Scripted assignments through creation, hydration and command commits."""

import json
import logging
from collections import defaultdict
from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from battle_agent_rl.scripted import ScriptedOpening
from battle_hexes_api.application import create_app
from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import (
    CommandReceipt,
    GameStateCodec,
    SavedGameIncompatibleError,
    StoredGame,
    SystemClock,
    create_command_identity,
)
from battle_hexes_core.scenario.scenario_loader import ScenarioData


FIELD = "scripted_objective_assignments"


@pytest.fixture
def setup_game(monkeypatch):
    def setup(
        blue, groups=(), objectives=(0, 8), blocker=(11, 2),
        types=("human", "scripted"), opening=None,
    ):
        hex_units = defaultdict(list)
        units = []
        for unit_id, faction, coords in [
            ("red", "red", blocker),
            *((unit_id, "blue", coords) for unit_id, coords in blue),
            *((unit_id, "blue", None) for _, _, _, ids in groups
              for unit_id in ids),
        ]:
            units.append({
                "id": unit_id, "name": unit_id, "faction": faction,
                "type": "Infantry", "attack": 1, "defense": 1, "movement": 1,
            })
            if coords is not None:
                hex_units[coords].append(unit_id)
        scenario = ScenarioData.model_validate({
            "id": "assignment-fixture", "version": "1", "name": "Assignments",
            "description": "A board for exercising scripted objectives.",
            "board_size": (12, 3),
            "factions": [
                {"id": "red", "name": "Red", "player": "Player 1",
                 "color": "#ff0000"},
                {"id": "blue", "name": "Blue", "player": "Player 2",
                 "color": "#0000ff"},
            ],
            "units": units,
            "hex_data": [
                {"coords": coords, "units": ids}
                for coords, ids in hex_units.items()
            ],
            "objectives": [
                {"coords": (row, 0), "points": 1, "type": "hold"}
                for row in objectives
            ],
            "reinforcements": [
                {"id": group, "arrival_turn": turn, "units": ids,
                 "entry_location": {"mode": "fixed", "coords": coords}}
                for group, turn, coords, ids in groups
            ],
        })
        monkeypatch.setattr(
            "battle_hexes_api.gamecreator.load_scenario",
            lambda _: scenario.to_core(),
        )
        monkeypatch.setattr(
            "battle_hexes_api.game_routes.load_scenario",
            lambda _: scenario.to_core(),
        )
        monkeypatch.setattr(
            "battle_hexes_api.command_adapters.serializers.load_scenario_data",
            lambda _: scenario,
        )
        game = GameCreator.create_sample_game(
            scenario.id, types, scripted_opening=opening,
        )
        return game, GameStateCodec(scenario_loader=lambda _: scenario)

    return setup


def _snapshot(game, codec):
    now = SystemClock().now()
    return StoredGame(
        game_id=str(game.id), version=1, state_schema_version=1,
        scenario_id=game.scenario_id, scenario_version="1",
        state=codec.encode(game, scenario_version="1"),
        updated_at=now, expires_at=now + 600,
    )


def _seed(repository, snapshot):
    repository.create_game(snapshot, CommandReceipt(
        identity=create_command_identity("seed", "POST", "/games", None, {}),
        game_id=snapshot.game_id, game_version=1, status_code=200,
        content_type="application/json", response_body=b"{}",
        response_headers={},
        created_at=snapshot.updated_at, expires_at=snapshot.expires_at,
    ))


def _command(client, snapshot, command, payload=None):
    response = client.post(
        f"/games/{snapshot.game_id}/{command}", json=payload,
        headers={
            "Idempotency-Key": command,
            "Expected-Game-Version": str(snapshot.version),
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _end_turn_on_disk(game, codec):
    snapshot = _snapshot(game, codec)
    positions = [
        {"id": unit.id, "row": unit.row, "column": unit.column}
        for unit in game.board.get_units()
    ]
    with TestClient(create_app(codec=codec)) as client:
        repo = client.app.state.game_repository
        _seed(repo, snapshot)
        result = _command(client, snapshot, "end-turn", {"units": positions})
        saved = repo.load_game(snapshot.game_id)
        assert saved.version == snapshot.version + 1
        replay = _command(client, snapshot, "end-turn", {"units": positions})
        assert replay == result
        assert repo.load_game(snapshot.game_id) == saved
        return saved, codec.decode(saved)


def test_creation_and_reload_keep_independent_targets_after_displacement(
    setup_game,
):
    game, codec = setup_game(
        [("a", (3, 0)), ("b", (7, 0))], types=("scripted", "scripted"),
    )
    first, second = game.players
    assert first.objective_assignments() == {"red": (8, 0)}
    expected = {"a": (0, 0), "b": (8, 0)}
    assert second.objective_assignments() == expected
    game.board.get_unit_by_id("a").set_coords(7, 0)
    game.board.get_unit_by_id("b").set_coords(1, 0)

    snapshot = _snapshot(game, codec)
    restored = codec.decode(snapshot)

    assert codec.encode(restored, scenario_version="1") == snapshot.state
    assert restored.players[1].objective_assignments() == expected
    plans = restored.players[1].movement()
    assert [(p.unit.id, p.path[-1].row) for p in plans] == [("a", 6), ("b", 2)]


def test_losses_leave_only_surviving_targets_in_the_save(setup_game):
    game, codec = setup_game([
        ("a", (0, 0)), ("b", (1, 0)), ("c", (7, 0)), ("d", (8, 0)),
    ])
    game.board.remove_units(game.board.get_unit_by_id(i) for i in ("a", "b"))
    game.board.get_unit_by_id("c").set_coords(2, 0)

    snapshot = _snapshot(game, codec)
    restored = codec.decode(snapshot)

    assert restored.players[1].objective_assignments() == {
        "c": (8, 0), "d": (8, 0),
    }
    records = json.loads(snapshot.state)[FIELD]
    assert [r["unit_id"] for r in records] == ["c", "d"]


def test_groups_commit_sequential_assignments_even_for_the_inactive_seat(
    setup_game,
):
    game, codec = setup_game(
        [(f"initial{i}", (row, 0))
         for i, row in enumerate([0, 0, 4, 4, 8, 8])],
        groups=[
            ("first", 2, (2, 0), ["r3", "r2", "r1"]),
            ("second", 2, (6, 0), ["r0"]),
        ],
        objectives=(0, 4, 8),
    )
    game.board.remove_units(
        game.board.get_unit_by_id(f"initial{i}") for i in (3, 4, 5)
    )
    game.board.get_unit_by_id("initial2").set_coords(9, 0)
    game.next_player()
    game.current_phase = "end_turn"

    saved, restored = _end_turn_on_disk(game, codec)

    assert restored.current_player is restored.players[0]
    assert restored.players[1].objective_assignments() == {
        "initial0": (0, 0), "initial1": (0, 0), "initial2": (4, 0),
        "r0": (4, 0), "r1": (8, 0), "r2": (4, 0), "r3": (8, 0),
    }
    assert [a["unit_id"] for a in json.loads(saved.state)[FIELD]] == [
        "initial0", "initial1", "initial2", "r0", "r1", "r2", "r3",
    ]


def test_turn_one_arrival_is_in_initial_balance_but_blocked_retry_is_not(
    setup_game,
):
    game, codec = setup_game(
        [("a", (4, 0))], blocker=(2, 1), objectives=(0, 10),
        groups=[
            ("immediate", 1, (1, 0), ["initial"]),
            ("blocked", 1, (2, 1), ["delayed"]),
            ("future", 4, (6, 0), ["pending"]),
        ],
    )
    expected = {"a": (10, 0), "initial": (0, 0)}
    assert game.players[1].objective_assignments() == expected

    game.board.get_unit_by_id("red").set_coords(11, 2)
    game.next_player()
    game.current_phase = "end_turn"
    _, restored = _end_turn_on_disk(game, codec)

    assert restored.players[1].objective_assignments() == {
        **expected, "delayed": (0, 0),
    }
    history = restored.reinforcements_deployer.game_log
    assert [event.outcome for event in history] == [
        "arrived", "blocked", "arrived",
    ]


def test_legacy_save_seeds_from_restored_positions_without_writing_on_read(
    setup_game,
):
    game, codec = setup_game(
        [("a", (3, 0))], groups=[
            ("immediate", 1, (7, 0), ["arrived"]),
            ("future", 3, (5, 0), ["pending"]),
        ],
    )
    game.board.get_unit_by_id("a").set_coords(7, 0)
    game.board.get_unit_by_id("arrived").set_coords(1, 0)
    game.next_player()
    snapshot = _snapshot(game, codec)
    document = json.loads(snapshot.state)
    del document[FIELD]
    legacy = replace(snapshot, state=json.dumps(document).encode())

    with TestClient(create_app(codec=codec)) as client:
        repo = client.app.state.game_repository
        _seed(repo, legacy)
        expected = {"a": (8, 0), "arrived": (0, 0)}
        for _ in range(2):
            response = client.get(f"/games/{legacy.game_id}")
            assert response.status_code == 200
            assert response.json()["gameVersion"] == legacy.version
            assert "scriptedObjectiveAssignments" not in response.json()
            assert repo.load_game(legacy.game_id) == legacy
            assert codec.decode(legacy).players[1].objective_assignments() == (
                expected
            )

        _command(client, legacy, "movement")
        saved = repo.load_game(legacy.game_id)
        assert saved.version == legacy.version + 1
        assert json.loads(saved.state)[FIELD] == [
            {"unit_id": "a", "row": 8, "column": 0},
            {"unit_id": "arrived", "row": 0, "column": 0},
        ]


@pytest.mark.parametrize("records", [
    None, [], [("a", 0), ("a", 8)], [("pending", 0)], [("red", 0)], [("a", 1)],
])
def test_present_invalid_assignment_never_falls_back(setup_game, records):
    game, codec = setup_game(
        [("a", (3, 0))], groups=[("future", 3, (5, 0), ["pending"])],
    )
    snapshot = _snapshot(game, codec)
    document = json.loads(snapshot.state)
    document[FIELD] = None if records is None else [
        {"unit_id": unit_id, "row": row, "column": 0}
        for unit_id, row in records
    ]
    corrupt = replace(snapshot, state=json.dumps(document).encode())

    with pytest.raises(SavedGameIncompatibleError):
        codec.decode(corrupt)


def test_non_scripted_game_omits_and_rejects_assignment_field(setup_game):
    game, codec = setup_game([("a", (3, 0))], types=("human", "human"))
    snapshot = _snapshot(game, codec)
    document = json.loads(snapshot.state)
    assert FIELD not in document
    assert codec.encode(codec.decode(snapshot), scenario_version="1") == (
        snapshot.state
    )

    document[FIELD] = []
    with pytest.raises(SavedGameIncompatibleError):
        codec.decode(replace(snapshot, state=json.dumps(document).encode()))


@pytest.mark.parametrize("objectives", [(), (0, 8)])
def test_initially_empty_side_loads_and_handles_first_arrival(
    setup_game, objectives, monkeypatch,
):
    monkeypatch.setattr("battle_agent_rl.scripted.opening.randbits",
                        lambda _: pytest.fail("requested entropy"))
    game, codec = setup_game(
        [], groups=[("first", 2, (4, 0), ["reserve"])], objectives=objectives,
        opening=ScriptedOpening(mode="randomized"),
    )
    snapshot = _snapshot(game, codec)
    assert json.loads(snapshot.state)[FIELD] == []
    restored = codec.decode(snapshot)
    restored.next_player()
    restored.next_player()
    reloaded = codec.decode(_snapshot(restored, codec))
    scripted = reloaded.players[1]

    assert scripted.objective_assignments() == (
        {"reserve": (0, 0)} if objectives else {}
    )
    if not objectives:
        assert scripted.movement() == []


def test_randomized_start_uses_turn_one_arrivals_and_later_keeps_targets(
    setup_game, monkeypatch, caplog,
):
    logger = "uvicorn.error.scripted_reinforcements"
    caplog.set_level(logging.INFO, logger=logger)

    def last_rank(stop):
        assert stop == 9  # Three active units, three objectives.
        return stop - 1

    monkeypatch.setattr("battle_agent_rl.scripted.opening.Random",
                        lambda _: SimpleNamespace(randrange=last_rank))
    game, codec = setup_game(
        [("a", (1, 0)), ("b", (3, 0))], objectives=(0, 4, 8),
        blocker=(8, 0),
        groups=[
            ("immediate", 1, (7, 0), ["turn-one"]),
            ("blocked", 1, (8, 0), ["delayed"]),
            ("future", 4, (9, 0), ["pending"]),
        ],
        opening=ScriptedOpening(mode="randomized", balanced_probability=0),
    )
    assert game.players[1].objective_assignments() == dict.fromkeys(
        ("a", "b", "turn-one"), (0, 0),
    )
    assert not any(record.name == logger for record in caplog.records)
    monkeypatch.setattr(
        "battle_agent_rl.scripted.opening.sample_objective_quotas",
        lambda *args: pytest.fail("rerolled the starting quotas"),
    )

    game.board.remove_units(game.board.get_unit_by_id("b"))
    game.board.get_unit_by_id("a").set_coords(10, 0)
    game.board.get_unit_by_id("red").set_coords(0, 0)
    game.next_player()
    game.current_phase = "end_turn"
    saved, restored = _end_turn_on_disk(game, codec)

    expected = {"a": (0, 0), "turn-one": (0, 0), "delayed": (8, 0)}
    assert restored.players[1].objective_assignments() == expected
    assert [a["unit_id"] for a in json.loads(saved.state)[FIELD]] == [
        "a", "delayed", "turn-one",
    ]
    logs = [record for record in caplog.records if record.name == logger]
    assert len(logs) == 1
    assert logs[0].levelno == logging.INFO
    assert str(restored.id) in logs[0].getMessage()
    assert logs[0].args[-1] == {"delayed": (8, 0)}


def test_randomized_balanced_rank_differs_from_legacy_and_baseline(
    setup_game, monkeypatch,
):
    monkeypatch.setattr(
        "battle_agent_rl.scripted.opening.Random",
        lambda _: SimpleNamespace(randrange=lambda stop: stop - 1),
    )
    units = [(str(i), (row, 0)) for i, row in enumerate((0, 5, 5, 10, 10))]
    opening = ScriptedOpening(mode="randomized", balanced_probability=1)
    game, codec = setup_game(units, objectives=(0, 5, 10), opening=opening)
    assert tuple(game.players[1].objective_assignment_counts().values()) == (
        2, 2, 1,
    )
    snapshot = _snapshot(game, codec)
    document = json.loads(snapshot.state)
    del document[FIELD]
    legacy = replace(snapshot, state=json.dumps(document).encode())
    monkeypatch.setattr(
        "battle_agent_rl.scripted.opening.sample_objective_quotas",
        lambda *args: pytest.fail("legacy or deterministic mode sampled"),
    )
    baseline, _ = setup_game(
        units, objectives=(0, 5, 10), opening=ScriptedOpening(),
    )
    for restored in [baseline, codec.decode(legacy), codec.decode(legacy)]:
        assert restored.players[1].objective_assignments() == dict(units)


def test_randomized_deployed_side_with_no_objectives_skips_sampling(
    setup_game, monkeypatch,
):
    monkeypatch.setattr(
        "battle_agent_rl.scripted.opening.sample_objective_quotas",
        lambda *args: pytest.fail("sampled an opening with no objectives"),
    )
    game, codec = setup_game(
        [("a", (1, 0))], objectives=(),
        opening=ScriptedOpening(mode="randomized"),
    )
    assert game.players[1].movement() == []
    assert json.loads(_snapshot(game, codec).state)[FIELD] == []
