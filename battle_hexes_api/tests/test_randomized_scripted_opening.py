import logging
import random
from itertools import product
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from battle_agent_rl.scripted import ScriptedOpening, ScriptedPlayer
from battle_hexes_api.application import create_app
from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_core.game.board import Board


CROSSROADS = "d_day_crossroads"
OBJECTIVES = ((2, 3), (3, 15), (6, 9))
OPENING_RNG = "battle_agent_rl.scripted.opening.Random"
OPENING_LOGGER = "uvicorn.error.scripted_opening"


def _force_crossroads_split(monkeypatch, quotas):
    unbalanced = [
        v for v in product(range(7), repeat=3)
        if sum(v) == 6 and v != (2, 2, 2)
    ]
    rank = unbalanced.index(quotas)

    def draw(stop):
        if stop == 2:
            return 1  # Select the unbalanced family at the default 50%.
        assert stop == len(unbalanced)
        return rank

    monkeypatch.setattr(
        OPENING_RNG, lambda _: SimpleNamespace(randrange=draw),
    )


@pytest.mark.parametrize(("quotas", "target"), list(zip(
    [(6, 0, 0), (0, 6, 0), (0, 0, 6)], OBJECTIVES,
)))
def test_crossroads_all_in_splits_keep_movement_legal(
    monkeypatch, quotas, target,
):
    _force_crossroads_split(monkeypatch, quotas)
    game = GameCreator.create_sample_game(
        CROSSROADS, ["scripted", "human"],
        scripted_opening=ScriptedOpening(mode="randomized", seed=0),
    )
    player = game.players[0]
    units = sorted(game.board.get_units_for_player(player), key=lambda u: u.id)
    expected = {unit.id: target for unit in units}
    assert len(expected) == 6
    assert player.objective_assignments() == expected
    assert game.board.stacking_limit == 2

    # Make the open objective full; the other two already have enemy units.
    if target == OBJECTIVES[0]:
        for unit in units[:2]:
            unit.set_coords(*target)
    row, column = target
    adjacent = units[2]
    adjacent.set_coords(row, column - 1)
    target_hex = game.board.get_hex(*target)

    plans = player.movement()
    assert all(plan.unit is not adjacent for plan in plans)
    assert all(target_hex not in plan.path for plan in plans)
    assert all(
        Board.hex_distance(plan.path[-1], target_hex)
        < Board.hex_distance(plan.path[0], target_hex)
        for plan in plans
    )
    game.apply_movement_plans(plans)
    assert len(game.board.get_units_at(*target)) <= 2
    assert player.objective_assignments() == expected


def test_seeded_factory_reproduces_both_sides_without_using_game_rng(
    monkeypatch,
):
    def unexpected_draw(*args):
        pytest.fail("opening used shared combat or defensive-fire randomness")

    monkeypatch.setattr(random, "random", unexpected_draw)
    opening = ScriptedOpening(mode="randomized", seed=0)
    previous_state = random.getstate()
    snapshots = []
    game_ids = []
    try:
        for seed, types in (
            (17, ["scripted", "scripted"]),
            (91, ["scripted", "scripted"]),
            (52, ["human", "scripted"]),
        ):
            state = random.Random(seed).getstate()
            random.setstate(state)
            game = GameCreator.create_sample_game(
                CROSSROADS, types, scripted_opening=opening,
            )
            assert random.getstate() == state
            game_ids.append(game.id)
            snapshots.append([p.objective_assignments() for p in game.players
                              if isinstance(p, ScriptedPlayer)])
    finally:
        random.setstate(previous_state)

    assert len(set(game_ids)) == 3
    assert snapshots[0] == snapshots[1]
    assert list(map(len, snapshots[0])) == [6, 3]
    assert snapshots[2] == snapshots[0][1:]


def test_browser_creation_randomizes_and_replay_reuses_the_committed_opening(
    monkeypatch, caplog,
):
    _force_crossroads_split(monkeypatch, (6, 0, 0))
    request = {
        "headers": {"Idempotency-Key": "randomized-opening"},
        "json": {"scenarioId": CROSSROADS,
                 "playerTypes": ["scripted", "human"]},
    }

    caplog.set_level(logging.INFO, logger=OPENING_LOGGER)
    with TestClient(create_app()) as client:
        state = client.app.state
        created = client.post("/games", **request)
        assert created.status_code == 200, created.text
        game_id = created.json()["id"]
        first = state.game_repository.load_game(game_id)

        def unexpected_draw(*args):
            pytest.fail("restoring or replaying the game sampled an opening")

        monkeypatch.setattr(
            "battle_agent_rl.scripted.opening.sample_objective_quotas",
            unexpected_draw,
        )
        assert client.post("/games", **request).content == created.content
        assert state.game_repository.load_game(game_id) == first
        assert client.get(f"/games/{game_id}").status_code == 200
        restored = state.game_state_codec.decode(first)
        expected = restored.players[0].objective_assignments()
        assert len(expected) == 6 and set(expected.values()) == {OBJECTIVES[0]}

        path = f"/games/{game_id}/movement"
        headers = {"Idempotency-Key": "move", "Expected-Game-Version": "1"}
        moved = client.post(path, headers=headers)
        assert moved.status_code == 200, moved.text
        second = state.game_repository.load_game(game_id)
        assert second.version == 2
        assert client.post(path, headers=headers).content == moved.content
        assert state.game_repository.load_game(game_id) == second
        restored = state.game_state_codec.decode(second)
        assert restored.players[0].objective_assignments() == expected

    logs = [record for record in caplog.records
            if record.name == OPENING_LOGGER]
    assert [record.levelno for record in logs] == [logging.INFO]
    assert "mode=randomized split=6/0/0 assignments=" in logs[0].getMessage()
    assert logs[0].args[-1] == dict(zip(OBJECTIVES, (6, 0, 0)))
