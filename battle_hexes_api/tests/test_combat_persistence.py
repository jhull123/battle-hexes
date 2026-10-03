"""Regression coverage for saving real combat outcomes through the API."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from battle_hexes_api.application import create_app
from battle_hexes_api.command_adapters import CreateGameResponseSerializer
from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import (
    CommandRequest,
    CreatedGame,
    EncodedItemBudget,
    GameCommandService,
    GameRepositoryInMemory,
    GameStateCodec,
    InMemoryItemSizer,
    SystemClock,
)
from battle_hexes_api.schemas import SparseBoard
from battle_hexes_core.combat.combatsolver import CombatSolver
from battle_hexes_core.scenario.scenario_loader import load_scenario_data


@pytest.mark.parametrize(
    ("die_roll", "expected_effect", "expected_state"),
    [
        (1, "retreated_units", "in_progress"),
        (6, "eliminated_units", "completed"),
    ],
)
def test_combat_commits_and_round_trips_real_unit_outcomes(
    die_roll, expected_effect, expected_state
):
    clock = SystemClock()
    codec = GameStateCodec()
    repository = GameRepositoryInMemory(
        clock, InMemoryItemSizer(), EncodedItemBudget()
    )
    game = GameCreator.create_sample_game("elim_1", ["human", "random"])
    red = next(
        unit for unit in game.board.get_units()
        if unit.get_name() == "Red Unit"
    )
    red.set_coords(8, 8)
    red.current_turn_movement_points_remaining = 2
    game.end_movement()
    scenario_version = load_scenario_data("elim_1").version
    service = GameCommandService(repository, codec, clock)
    service.create(
        CommandRequest(
            "seed-combat-1234", "POST", "/games", {}, None
        ),
        lambda: CreatedGame(game, "elim_1", scenario_version),
        CreateGameResponseSerializer(scenario_version),
    )
    game_id = str(game.id)
    board = SparseBoard.from_game(game).model_dump(
        by_alias=True, mode="json"
    )

    with patch.object(CombatSolver, "_roll_die", return_value=die_roll):
        with TestClient(
            create_app(clock=clock, repository=repository, codec=codec)
        ) as client:
            response = client.post(
                f"/games/{game_id}/combat",
                json=board,
                headers={
                    "Idempotency-Key": "resolve-combat-1234",
                    "Expected-Game-Version": "1",
                },
            )
            loaded = client.get(f"/games/{game_id}")
            if expected_state == "completed":
                rejected = client.post(
                    f"/games/{game_id}/end-turn",
                    json=board,
                    headers={
                        "Idempotency-Key": "after-combat-1234",
                        "Expected-Game-Version": "2",
                    },
                )
                assert rejected.status_code == 409
                after_rejection = client.get(f"/games/{game_id}")
                assert after_rejection.content == loaded.content

    assert response.status_code == 200
    assert response.json()["gameVersion"] == 2
    assert loaded.status_code == 200
    assert loaded.json()["gameVersion"] == 2
    stored = repository.load_game(game_id)
    decoded = codec.decode(stored)
    event = decoded.combat_log[0]
    assert getattr(event, expected_effect) == ("Red Unit",)
    reencoded = codec.encode(decoded, scenario_version=scenario_version)
    assert reencoded == stored.state
    assert next(
        unit for unit in decoded.board.get_known_units()
        if unit.get_name() == "Red Unit"
    ).current_turn_movement_points_remaining == 2
    assert loaded.json()["gameStatus"]["state"] == expected_state
    if expected_state == "completed":
        assert loaded.json()["activePlayer"] is None
        assert loaded.json()["currentPhase"] is None
