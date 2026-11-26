"""A winning move must persist the final board, score and completed phase."""

import pytest
from fastapi.testclient import TestClient

from battle_hexes_api.application import create_app
from battle_hexes_api.command_adapters import CreateGameResponseSerializer
from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import CommandRequest, CreatedGame
from battle_hexes_core.scenario.scenario_loader import load_scenario_data
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer


MOVER = "Airborne Inf. E"


def _seed_crossroads_one_move_from_victory(client, player_type):
    scenario = load_scenario_data("d_day_crossroads")
    game = GameCreator.create_sample_game(
        scenario.id, [player_type, "scripted"],
    )
    for _ in range(4):
        game.next_player()  # Arrive at Airborne's turn 3 after deployment.

    positions = {
        "Airborne Inf. A": (3, 15),
        "Airborne Inf. B": (6, 9),
        MOVER: (2, 2),
    }
    for unit in game.board.get_units():
        if unit.id in positions:
            unit.set_coords(*positions[unit.id])
        else:
            game.board.remove_units(unit)
    ObjectiveScorer().recalculate_scenario_victory(game)
    assert game.get_game_status().state == "in_progress"
    scores = game.get_score_tracker().get_scores()
    assert scores == {"Player 1": 2, "Player 2": 1}

    client.app.state.game_command_service.create(
        CommandRequest("seed-crossroads", "POST", "/games", {}, None),
        lambda: CreatedGame(game, scenario.id, scenario.version),
        CreateGameResponseSerializer(scenario.version),
    )
    return f"/games/{game.id}"


def _assert_completed(game):
    assert game["gameVersion"] == 2
    assert game["scores"] == {"Player 1": 3, "Player 2": 0}
    assert game["gameStatus"]["state"] == "completed"
    assert game["gameStatus"]["winnerFactionId"] == "Airborne"
    assert game["activePlayer"] is None
    assert game["currentPhase"] is None
    assert game["pendingCombats"] == []
    mover = next(u for u in game["board"]["units"] if u["id"] == MOVER)
    assert (mover["row"], mover["column"]) == (2, 3)


@pytest.mark.parametrize(("player_type", "command"), [
    ("scripted", "movement"),
    ("human", "move"),
    ("human", "end-movement"),
])
def test_winning_move_commits_completed_snapshot(player_type, command):
    payload = None if command == "movement" else {
        "units": [{"id": MOVER, "row": 2, "column": 3}],
    }
    headers = {
        "Idempotency-Key": "take-final-objective",
        "Expected-Game-Version": "1",
    }
    with TestClient(create_app()) as client:
        url = _seed_crossroads_one_move_from_victory(client, player_type)
        command_url = f"{url}/{command}"

        response = client.post(command_url, json=payload, headers=headers)
        assert response.status_code == 200, response.text
        _assert_completed(response.json()["game"])

        reloaded = client.get(url)
        assert reloaded.status_code == 200, reloaded.text
        _assert_completed(reloaded.json())

        replay = client.post(command_url, json=payload, headers=headers)
        assert replay.status_code == 200
        assert replay.content == response.content
