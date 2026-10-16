"""Real trained artifact through the versioned API and detached state codec."""

import json
import random
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from battle_agent_rl.ppo.multi_unit_train import train
from battle_agent_rl.ppo.multi_unit_gym import predict_joint_action
from battle_agent_rl.ppo.playable_artifact import load_model
from battle_agent_rl.ppo.playable_environment import PlayableEnvironment
from battle_agent_rl.ppo.playable_scenario import slots_for_game
from battle_agent_rl.ppo.multi_unit_state import joint_mask, slot_observation
from battle_agent_rl.ppo.playable_turn import apply_order
from battle_hexes_api.application import create_app
from battle_hexes_api.command_adapters.ppo_order import PpoOrderAdapter
from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.ppo_state import capture_rng
from battle_hexes_api.persistence import (EncodedItemBudget,
                                          GameRepositoryInMemory, StoredGame,
                                          SystemClock)
from battle_hexes_api.persistence.game_state_codec import GameStateCodec
from battle_hexes_api.persistence.item_sizer import InMemoryItemSizer
from battle_hexes_api.persistence.errors import SavedGameIncompatibleError


@pytest.fixture(scope="module")
def artifact(tmp_path_factory):
    run_dir = tmp_path_factory.mktemp("ppo") / "trained"
    train(0, 16, 16, 8, run_dir)
    return run_dir


def _repository():
    clock = SystemClock()
    return GameRepositoryInMemory(clock, InMemoryItemSizer(),
                                  EncodedItemBudget())


def _create(client, types=None):
    return client.post("/games", headers={"Idempotency-Key": "create-ppo"},
                       json={"scenarioId": "ppo_9x9_experimental",
                             "playerTypes": types or
                             ["ppo-9x9-experimental", "human"]})


def _order(client, game_id, version, key):
    return client.post(f"/games/{game_id}/ppo/order", headers={
        "Idempotency-Key": key, "Expected-Game-Version": str(version)})


def _human_command(client, game_id, game, path, key):
    board = {"units": [
        {"id": unit["id"], "row": unit["row"],
         "column": unit["column"]} for unit in game["board"]["units"]]}
    response = client.post(f"/games/{game_id}/{path}", json=board,
                           headers={"Idempotency-Key": key,
                                    "Expected-Game-Version": str(
                                        game["gameVersion"])})
    assert response.status_code == 200, response.text
    return response.json()


def test_creation_requires_artifact_and_fixed_seats(
        artifact, monkeypatch, caplog):
    monkeypatch.delenv("BATTLE_HEXES_PPO_RUN_DIR", raising=False)
    with TestClient(create_app()) as client:
        assert _create(client).status_code == 503
        assert _create(
            client, ["human", "ppo-9x9-experimental"]).status_code == 422
    assert "BATTLE_HEXES_PPO_RUN_DIR is unset" in caplog.text

    monkeypatch.setenv(
        "BATTLE_HEXES_PPO_RUN_DIR", str(artifact / "missing-directory"))
    with TestClient(create_app()) as client:
        assert _create(client).status_code == 503
    assert "PPO artifact directory does not exist" in caplog.text

    monkeypatch.setenv("BATTLE_HEXES_PPO_RUN_DIR", str(artifact))
    with TestClient(create_app()) as client:
        response = client.post("/games", headers={"Idempotency-Key": "wrong"},
                               json={"scenarioId": "elim_1", "playerTypes":
                                     ["ppo-9x9-experimental", "human"]})
        assert response.status_code == 422


def test_training_and_live_adapter_share_initial_masked_decision(
        artifact, monkeypatch):
    monkeypatch.setenv("BATTLE_HEXES_PPO_RUN_DIR", str(artifact))
    game = GameCreator.create_sample_game(
        "ppo_9x9_experimental", ["ppo-9x9-experimental", "human"])
    game.ppo_rng = random.Random(0)
    game.defensive_fire_resolver.rng = game.ppo_rng
    slots = slots_for_game(game)
    pending = [True, True]
    observation = slot_observation(game, slots, pending, 50, game.players[0])
    mask = joint_mask(game, slots[:2], pending)
    env = PlayableEnvironment()
    state = env.reset(0)
    assert observation == state.observation
    assert mask == state.legal_action_mask
    model, _ = load_model(artifact)
    action = predict_joint_action(model, state.observation,
                                  state.legal_action_mask)
    result = PpoOrderAdapter()(game)
    destination = result.plan.path[-1]
    slot = next(i for i, unit in enumerate(slots[:2])
                if unit is result.plan.unit)
    assert action == slot * 81 + destination.row * 9 + destination.column
    assert not result.combats


def test_fire_retreat_and_rng_survive_hydration(artifact, monkeypatch):
    monkeypatch.setenv("BATTLE_HEXES_PPO_RUN_DIR", str(artifact))
    game = GameCreator.create_sample_game(
        "ppo_9x9_experimental", ["ppo-9x9-experimental", "human"])
    slots = slots_for_game(game)
    slots[2].set_coords(3, 4)
    slots[2].ended_last_friendly_turn_with_defensive_fire_eligibility = True
    game.ppo_rng = random.Random(1)
    game.defensive_fire_resolver.rng = game.ppo_rng
    pending = [True, True]
    _, fire, combat = apply_order(game, slots[:2], pending, 30,
                                  game.ppo_rng)
    assert fire[0].outcome == "retreat" and not combat
    game.ppo_state["pending_unit_ids"] = ["learner-1"]
    capture_rng(game)
    codec = GameStateCodec()
    stored = StoredGame(str(game.id), 2, 1, game.scenario_id, "1",
                        codec.encode(game, scenario_version="1"), 0, 100)
    restored = codec.decode(stored)
    assert restored.ppo_state["pending_unit_ids"] == ["learner-1"]
    assert restored.ppo_rng.getstate() == game.ppo_rng.getstate()
    assert restored.board.get_unit_by_id("learner-0").get_coords() == (4, 2)
    assert restored.defensive_fire_log[0].outcome == "retreated"


def _first_order(repo):
    with TestClient(create_app(repository=repo)) as client:
        created = _create(client)
        assert created.status_code == 200
        game_id = created.json()["id"]
        first = _order(client, game_id, 1, "first")
        assert first.status_code == 200
        assert first.json()["plan"]["unitId"] in (
            "learner-0", "learner-1")
        assert len(first.json()["game"]["ppoTurn"]["pendingUnitIds"]) == 1
        assert first.json()["ppoTurn"] == first.json()["game"]["ppoTurn"]
        assert _order(client, game_id, 1, "first").content == first.content
        stale = _order(client, game_id, 1, "new-stale")
        assert stale.status_code == 409
        assert stale.json()["code"] == "gameVersionConflict"
        stored = repo.load_game(game_id)
        first_state = json.loads(stored.state)
        assert first_state["ppo_state"]["pending_unit_ids"] == \
            first.json()["game"]["ppoTurn"]["pendingUnitIds"]
        return game_id, first


def test_mid_turn_restart_receipt_rng_and_handoff(artifact, monkeypatch):
    monkeypatch.setenv("BATTLE_HEXES_PPO_RUN_DIR", str(artifact))
    repo = _repository()
    game_id, first = _first_order(repo)
    with TestClient(create_app(repository=repo)) as client:
        loaded = client.get(f"/games/{game_id}")
        assert loaded.status_code == 200
        assert loaded.json()["ppoTurn"] == first.json()["game"]["ppoTurn"]
        assert _order(client, game_id, 1, "first").content == first.content
        second = _order(client, game_id, 2, "second")
        assert second.status_code == 200
        state = second.json()["game"]
        assert state["ppoTurn"]["pendingUnitIds"] == []
        assert state["activePlayer"] == "Opponent"
        assert state["currentPhase"] == "movement"
        assert repo.load_game(game_id).version == 3
        assert _order(client, game_id, 3, "wrong-phase").status_code == 409
        assert repo.load_game(game_id).version == 3
        forbidden = client.post(f"/games/{game_id}/movement", headers={
            "Idempotency-Key": "batch", "Expected-Game-Version": "3"})
        assert forbidden.status_code == 409
        board = {"units": [
            {"id": unit["id"], "row": unit["row"],
             "column": unit["column"]} for unit in state["board"]["units"]]}
        finish = client.post(f"/games/{game_id}/end-movement", json=board,
                             headers={"Idempotency-Key": "human-move",
                                      "Expected-Game-Version": "3"})
        assert finish.status_code == 200
        next_turn = client.post(f"/games/{game_id}/end-turn", json=board,
                                headers={"Idempotency-Key": "human-turn",
                                         "Expected-Game-Version": "4"})
        assert next_turn.status_code == 200
        assert next_turn.json()["ppoTurn"]["pendingUnitIds"] == [
            "learner-0", "learner-1"]
        assert repo.load_game(game_id).version == 5


def test_hydration_rejects_tampered_identity(artifact, monkeypatch):
    monkeypatch.setenv("BATTLE_HEXES_PPO_RUN_DIR", str(artifact))
    with TestClient(create_app()) as client:
        created = _create(client)
        stored = client.app.state.game_repository.load_game(
            created.json()["id"])
        state = json.loads(stored.state)
        state["ppo_state"]["pending_unit_ids"] = ["opponent-0"]
        corrupted = replace(stored, state=json.dumps(state).encode())
        with pytest.raises(SavedGameIncompatibleError):
            GameStateCodec().decode(corrupted)
        state["ppo_state"]["pending_unit_ids"] = ["learner-0", "learner-1"]
        state["units"][0]["movement_points_remaining"] = 0
        with pytest.raises(SavedGameIncompatibleError):
            GameStateCodec().decode(replace(
                stored, state=json.dumps(state).encode()))
        state["units"][0]["movement_points_remaining"] = 2
        state["ppo_state"]["checkpoint_digest"] = "0" * 64
        with pytest.raises(SavedGameIncompatibleError):
            GameStateCodec().decode(replace(
                stored, state=json.dumps(state).encode()))


def test_http_game_reaches_core_completion(artifact, monkeypatch):
    monkeypatch.setenv("BATTLE_HEXES_PPO_RUN_DIR", str(artifact))
    with TestClient(create_app()) as client:
        response = _create(client)
        assert response.status_code == 200
        game = response.json()
        game_id = game["id"]
        for step in range(300):
            if game["gameStatus"]["state"] == "completed":
                break
            if game["activePlayer"] == "Learner":
                response = _order(client, game_id, game["gameVersion"],
                                  f"ppo-completion-{step}")
                assert response.status_code == 200, response.text
                game = response.json()["game"]
            else:
                phase = game["currentPhase"]
                path = {"movement": "end-movement", "combat": "combat",
                        "end_turn": "end-turn"}[phase]
                result = _human_command(client, game_id, game, path,
                                        f"human-completion-{step}")
                game = result.get("game") or client.get(
                    f"/games/{game_id}").json()
        assert game["gameStatus"]["state"] == "completed"
        assert game["turnNumber"] <= 50
        assert game["currentPhase"] is None
        assert client.get(f"/games/{game_id}").json()["gameStatus"] == \
            game["gameStatus"]
