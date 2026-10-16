import json
import hashlib
import random

import pytest

from battle_agent_rl.ppo.multi_unit_evaluate import evaluate
from battle_agent_rl.ppo.multi_unit_gym import predict_joint_action
from battle_agent_rl.ppo.multi_unit_gym import MaskedMultiUnitEnv
from battle_agent_rl.ppo.multi_unit_state import joint_mask, slot_observation
from battle_agent_rl.ppo.multi_unit_train import train
from battle_agent_rl.ppo.playable_artifact import load_model
from battle_agent_rl.ppo.playable_environment import PlayableEnvironment
from battle_agent_rl.ppo.playable_scenario import create_game
from battle_agent_rl.ppo.playable_turn import apply_order


def test_core_loaded_horizon_and_early_cutoff():
    game, learner, opponent, slots = create_game(random.Random(0))
    assert game.turn_limit == 50
    assert [unit.get_coords() for unit in slots] == [
        (3, 2), (5, 2), (3, 6), (5, 6)]
    assert game.players == [learner, opponent]
    env = PlayableEnvironment(cycle_limit=1)
    state = env.reset(12)
    assert state.observation["remaining_cycles"] == [50]
    assert state.legal_action_mask[29] and state.legal_action_mask[128]
    state = env.step(29)
    assert not state.terminated and state.legal_action_mask[128]
    assert not state.legal_action_mask[29]
    state = env.step(128)
    assert state.truncated and state.info["core_status"] == "in_progress"
    assert state.observation["remaining_cycles"] == [49]


def test_core_turn_50_is_a_zero_score_draw():
    rng = random.Random(0)
    game, _, _, slots = create_game(rng)
    while game.get_game_status().state == "in_progress":
        if game.current_player is game.players[0]:
            side, actions = slots[:2], (29, 128)
        else:
            side, actions = slots[2:], (33, 132)
        pending = [True, True]
        for action in actions:
            apply_order(game, side, pending, action, rng)
    assert game.turn_number == 50
    assert game.get_game_status().winner_player_name is None
    assert game.score_tracker.get_scores() == {"Learner": 0, "Opponent": 0}
    assert game.current_phase is None


def test_live_fire_and_retreat_feed_next_pending_decision():
    rng = random.Random(1)
    game, learner, _, slots = create_game(rng)
    slots[2].set_coords(3, 4)
    slots[2].ended_last_friendly_turn_with_defensive_fire_eligibility = True
    pending = [True, True]
    _, fire, combats = apply_order(game, slots[:2], pending, 30, rng)
    assert len(fire) == 1 and fire[0].outcome == "retreat"
    assert not combats and game.current_phase == "movement"
    assert pending == [False, True]
    observation = slot_observation(game, slots, pending, 50, learner)
    mask = joint_mask(game, slots[:2], pending)
    assert observation["positions"][0][4 * 9 + 2] == 1
    assert observation["forced_retreat"][0] == 1
    assert observation["fire_spent"][2] == 1
    assert not any(mask[:81]) and any(mask[81:])


def test_trained_checkpoint_reloads_and_replays(tmp_path):
    run_dir = tmp_path / "trained"
    model, manifest = train(0, 16, 16, 8, run_dir)
    assert manifest["training"]["parameters_changed"]
    assert manifest["training"]["actual_timesteps"] == 16
    assert manifest["training"]["optimizer_updates"] == 20
    assert manifest["training"]["ppo_epochs"] == 10
    env = PlayableEnvironment()
    decision = env.reset(1000)
    before = predict_joint_action(model, decision.observation,
                                  decision.legal_action_mask)
    reloaded, _ = load_model(run_dir)
    assert predict_joint_action(reloaded, decision.observation,
                                decision.legal_action_mask) == before
    assert decision.legal_action_mask[before]
    report = evaluate(run_dir, range(1000, 1002), cycle_limit=1)
    assert report["counts"]["cutoff"] + sum(
        report["counts"][key] for key in ("win", "loss", "draw")) == 2
    assert all(row["coreStatus"] == "in_progress" for row in
               report["episodes"] if row["outcome"] == "cutoff")
    with pytest.raises(ValueError, match="disjoint"):
        evaluate(run_dir, [0])
    altered = json.loads((run_dir / "manifest.json").read_text())
    altered["contract"] = "battle-hexes-9x9-2slot-unit-destination-live-v1"
    (run_dir / "manifest.json").write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="Incompatible"):
        load_model(run_dir)
    (run_dir / "manifest.json").write_text(json.dumps(manifest))
    altered = {**manifest, "versions": {
        **manifest["versions"], "torch": "incompatible"}}
    (run_dir / "manifest.json").write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="Incompatible"):
        load_model(run_dir)
    (run_dir / "manifest.json").write_text(json.dumps(manifest))
    archive = run_dir / "checkpoint.zip"
    archive.write_bytes(b"invalid archive")
    with pytest.raises(ValueError, match="digest mismatch"):
        load_model(run_dir)


def test_v1_spaces_cannot_be_served_as_v2(tmp_path):
    from sb3_contrib import MaskablePPO
    from battle_agent_rl.ppo.playable_artifact import save_run

    run_dir = tmp_path / "v2"
    env = MaskedMultiUnitEnv(cycle_limit=3)
    v1 = MaskablePPO("MultiInputPolicy", env, device="cpu", n_steps=16,
                     batch_size=8)
    # A valid v2 manifest cannot make a v1 archive's spaces compatible.
    save_run(run_dir, v1, seed=0, total_timesteps=16, n_steps=16,
             batch_size=8, episode_seeds=[0], outcomes={}, changed=True)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["training"]["optimizer_updates"] = 1
    manifest_path.write_text(json.dumps(manifest))
    assert manifest["checkpoint"]["sha256"] == hashlib.sha256(
        (run_dir / "checkpoint.zip").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="spaces mismatch"):
        load_model(run_dir)
