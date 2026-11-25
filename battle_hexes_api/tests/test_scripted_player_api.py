from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from battle_agent_rl.scripted import ScriptedPlayer
from battle_hexes_api.application import create_app
from battle_hexes_api.command_adapters import CreateGameResponseSerializer
from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import (
    CommandRequest, CreatedGame, GameCommandService, GameStateCodec,
    SystemClock,
)
from battle_hexes_core.combat.combatsolver import CombatSolver
from battle_hexes_core.scenario.scenario_loader import load_scenario_data


def _headers(key, version=None):
    headers = {"Idempotency-Key": key}
    if version is not None:
        headers["Expected-Game-Version"] = str(version)
    return headers


def _command(client, game, command, key=None):
    body = None if command == "movement" else {
        "units": [
            {field: unit[field] for field in ("id", "row", "column")}
            for unit in game["board"]["units"]
        ],
    }
    response = client.post(
        f"/games/{game['id']}/{command}", json=body,
        headers=_headers(key or command, game["gameVersion"]),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _positions(game):
    return {unit["id"]: (unit["row"], unit["column"])
            for unit in game["board"]["units"]}


def _assert_empty_movement(before, response):
    assert response["plans"] == []
    assert response["defensiveFireEvents"] == []
    assert response["game"]["currentPhase"] == "movement"
    assert _positions(response["game"]) == _positions(before)


def test_player_type_catalog_exposes_scripted():
    with TestClient(create_app()) as client:
        response = client.get("/player-types")
    assert response.status_code == 200
    assert {"id": "scripted", "name": "Scripted Player"} in response.json()


@pytest.mark.parametrize("scenario_id", ["elim_1", "d_day_crossroads"])
def test_scripted_in_both_seats_survives_load_and_hands_off(scenario_id):
    with TestClient(create_app()) as client:
        created = client.post(
            "/games", headers=_headers("create-scripted"),
            json={"scenarioId": scenario_id,
                  "playerTypes": ["scripted", "scripted"]},
        )
        assert created.status_code == 200, created.text
        game_id = created.json()["id"]
        loaded = client.get(f"/games/{game_id}")
        assert loaded.status_code == 200, loaded.text
        game = loaded.json()
        for payload in [created.json(), game]:
            assert payload["playerTypeIds"] == ["scripted", "scripted"]
            assert [p["type"] for p in payload["players"]] == [
                "Computer", "Computer"]
        saved = client.app.state.game_repository.load_game(game_id)
        restored = GameStateCodec().decode(saved)
        assert all(isinstance(p, ScriptedPlayer) for p in restored.players)

        first = _command(client, game, "movement")
        _assert_empty_movement(game, first)
        assert _command(client, game, "movement") == first
        stale = client.post(f"/games/{game_id}/movement",
                            headers=_headers("stale", game["gameVersion"]))
        assert stale.status_code == 409
        closing = _command(client, first["game"], "end-movement")["game"]
        assert closing["pendingCombats"] == []
        assert closing["currentPhase"] == "end_turn"
        handoff = _command(client, closing, "end-turn")
        assert handoff["activePlayer"] == game["players"][1]["name"]
        second = _command(client, handoff, "movement", key="second-movement")
        _assert_empty_movement(handoff, second)


def _seed_adjacent_units(client):
    game = GameCreator.create_sample_game("elim_1", ["scripted", "human"])
    game.board.units["red_unit_1"].set_coords(8, 8)
    scenario_version = load_scenario_data("elim_1").version
    service = GameCommandService(client.app.state.game_repository,
                                 GameStateCodec(), SystemClock())
    service.create(
        CommandRequest("seed-scripted", "POST", "/games", {}, None),
        lambda: CreatedGame(game, "elim_1", scenario_version),
        CreateGameResponseSerializer(scenario_version),
    )
    response = client.get(f"/games/{game.id}")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("die_roll, completed", [(1, False), (6, True)])
def test_no_orders_do_not_skip_pending_combat(die_roll, completed):
    with TestClient(create_app()) as client:
        start = _seed_adjacent_units(client)
        moved = _command(client, start, "movement")
        _assert_empty_movement(start, moved)
        closing = _command(client, moved["game"], "end-movement")["game"]
        assert closing["currentPhase"] == "combat"
        assert closing["pendingCombats"]

        with patch.object(CombatSolver, "_roll_die", return_value=die_roll):
            combat = _command(client, closing, "combat")
        assert combat["lastCombatResults"]
        if completed:
            assert combat["gameStatus"]["state"] == "completed"
            assert combat["currentPhase"] is None
        else:
            assert combat["currentPhase"] == "end_turn"
            game = client.get(f"/games/{closing['id']}").json()
            handoff = _command(client, game, "end-turn")
            assert handoff["currentPhase"] == "movement"
            assert handoff["activePlayer"] == start["players"][1]["name"]
