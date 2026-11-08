"""08c initialized-policy legality and thin Gym ending semantics."""

from copy import deepcopy
import pickle

import numpy as np
import pytest
import torch
from gymnasium.utils.passive_env_checker import (
    env_reset_passive_checker, env_step_passive_checker,
)

from battle_agent_rl.ppo.decision_controller import choose_action
from battle_agent_rl.ppo.scenario_gym import MaskedScenarioEnv
from battle_agent_rl.ppo.scenario_manifest import POLICY_KWARGS
from battle_agent_rl.ppo.scenario_policy import ScenarioPolicy
from battle_agent_rl.ppo.scenario_task import ScenarioTask


def hold(env):
    game_env = env.game_env
    return env.step(choose_action(game_env.binding, game_env.pending,
                                  "hold", None))


@pytest.mark.parametrize("cap", [2, None])
def test_gym_live_spaces_seed_sequence_and_endings(crossroads_task, cap):
    env = MaskedScenarioEnv(crossroads_task, cap, "hold", training_seed=17)
    with pytest.raises(RuntimeError, match="Reset"):
        env.action_masks()
    obs, info = env.reset()
    assert info["episode_seed"] == 17
    assert info["decision_count"] == 0 and len(info["orders"]) == 6
    assert env.observation_space.contains(obs)
    while True:
        obs, reward, terminated, truncated, info = hold(env)
        assert env.observation_space.contains(obs)
        mask = env.action_masks()
        assert mask.dtype == np.bool_ and mask.shape == (1620,)
        if terminated or truncated:
            break
        assert mask.any() and reward == 0
    assert not mask.any() and not obs["pending"].any()
    assert terminated == (cap is None) and truncated == (cap is not None)
    assert info["core_status"] == (
        "completed" if terminated else "in_progress")
    assert obs["remaining_cycles"].tolist() == (
        [1] if terminated else [6])
    assert reward == (1 if terminated else 0)
    with pytest.raises(RuntimeError, match="Reset"):
        env.step(69)
    assert env.reset()[1]["episode_seed"] == 18
    assert env.reset(seed=4)[1]["episode_seed"] == 4
    assert env.reset()[1]["episode_seed"] == 5


def test_gym_tuples_and_invalid_actions_preserve_state(crossroads_task):
    env = MaskedScenarioEnv(crossroads_task, 1, "hold")
    # The generic checker samples unmasked illegal actions; check the same
    # tuple contracts with a legal action instead of weakening validation.
    env_reset_passive_checker(env, seed=17)
    env_step_passive_checker(env, 69)
    env.reset(seed=17)
    before = pickle.dumps(env.game_env.__dict__)
    for action in (True, -1, 1620, 69.0, np.array([69]), 988):
        with pytest.raises(ValueError):
            env.step(action)
        assert pickle.dumps(env.game_env.__dict__) == before
    mask = env.action_masks()
    mask[:] = False
    assert env.action_masks().any()  # No externally mutable mask cache.


def test_initialized_policy_reachable_masks_and_unchanged_weights(
        crossroads_task, initialized_scenario_model):
    model = initialized_scenario_model
    assert model.policy_kwargs == POLICY_KWARGS
    assert model.policy.mlp_extractor.policy_net[0].out_features == 64
    assert model.policy.mlp_extractor.value_net[2].out_features == 64
    assert isinstance(model.policy.mlp_extractor.policy_net[1], torch.nn.Tanh)
    before = [p.detach().clone() for p in model.policy.parameters()]
    policy = ScenarioPolicy(model, crossroads_task)
    env = MaskedScenarioEnv(crossroads_task, opponent_policy="hold")
    obs, _ = env.reset(seed=0)
    counts = set()
    while env.game_env.game.turn_number <= 3:
        mask = env.action_masks()
        counts.add(int(obs["pending"].sum()))
        for deterministic in (True, False):
            for _ in range(5):
                action = policy.predict(obs, mask, deterministic=deterministic)
                assert mask[action]
        if obs["pending"].tolist() == [0, 0, 1, 0, 0]:
            assert np.flatnonzero(mask).tolist() == [765]
        obs, *_ = hold(env)
    assert {1, 3, 5}.issubset(counts)
    assert all(torch.equal(a, b) for a, b in zip(
        before, model.policy.parameters()))


def test_initialized_policy_after_live_casualties(
        crossroads_task, initialized_scenario_model):
    env = MaskedScenarioEnv(crossroads_task, opponent_policy="hold")
    env.reset(seed=0)
    game_env = env.game_env
    a, b = game_env.binding.slots[:2]
    defenders = game_env.binding.slots[5:7]
    a.set_coords(0, 2)
    b.set_coords(0, 4)
    defenders[0].set_coords(1, 1)
    defenders[1].set_coords(1, 3)
    game_env.rng.random = lambda: 0.0
    env.step(1)
    obs, _, terminated, truncated, info = env.step(327)
    assert info["defensive_fire"][0].outcome == "eliminated"
    assert obs["unit_status"][:3].tolist() == [2, 2, 1]
    assert not terminated and not truncated
    policy = ScenarioPolicy(initialized_scenario_model, crossroads_task)
    assert policy.predict(obs, env.action_masks()) == 765


@pytest.mark.parametrize("field,value", [
    ("contract", "battle-hexes-crossroads-airborne-draft-v1"),
    ("learner_seat", 0), ("slot_ids", ["wrong"]),
    ("action_space", {"type": "Discrete", "n": 162}),
])
def test_incompatible_binding_rejects_before_prediction(
        crossroads_task, initialized_scenario_model, monkeypatch,
        field, value):
    model = initialized_scenario_model
    interface = deepcopy(model.scenario_interface)
    interface[field] = value
    monkeypatch.setattr(model, "scenario_interface", interface)
    monkeypatch.setattr(model, "predict",
                        lambda *a, **k: pytest.fail("predicted"))
    with pytest.raises(ValueError, match="Incompatible"):
        ScenarioPolicy(model, crossroads_task)


def test_wrong_spaces_empty_mask_and_invalid_predictions_reject(
        crossroads_task, initialized_scenario_model, monkeypatch):
    model = initialized_scenario_model
    policy = ScenarioPolicy(model, crossroads_task)
    env = MaskedScenarioEnv(crossroads_task)
    obs, _ = env.reset(seed=0)
    monkeypatch.setattr(model, "predict",
                        lambda *a, **k: pytest.fail("predicted"))
    for mask in (np.zeros(1620, dtype=bool), np.ones(162, dtype=bool),
                 np.ones(1620, dtype=np.int8)):
        with pytest.raises(ValueError, match="mask"):
            policy.predict(obs, mask)
    bad_obs = {**obs, "pending": np.ones(4, dtype=np.int8)}
    with pytest.raises(ValueError, match="observation"):
        policy.predict(bad_obs, env.action_masks())
    monkeypatch.setattr(model, "predict", lambda *a, **k: (988, None))
    with pytest.raises(ValueError, match="illegal"):
        policy.predict(obs, env.action_masks())
    monkeypatch.setattr(model, "action_space", env.action_space.__class__(162))
    with pytest.raises(ValueError, match="spaces"):
        ScenarioPolicy(model, crossroads_task)


@pytest.mark.parametrize("legacy_size", [5, 9])
def test_legacy_initialized_policy_and_changed_runtime_seat_reject(
        crossroads_task, initialized_scenario_model, legacy_size):
    from sb3_contrib import MaskablePPO
    from battle_agent_rl.ppo.gym_env import MaskedBattleHexesEnv
    from battle_agent_rl.ppo.multi_unit_gym import MaskedMultiUnitEnv
    env = (MaskedBattleHexesEnv() if legacy_size == 5 else
           MaskedMultiUnitEnv(playable=True))
    legacy = MaskablePPO("MultiInputPolicy", env,
                         n_steps=2, batch_size=2, device="cpu", seed=0)
    with pytest.raises(ValueError, match="Incompatible"):
        ScenarioPolicy(legacy, crossroads_task)
    with pytest.raises(ValueError, match="Incompatible"):
        ScenarioPolicy(initialized_scenario_model,
                       ScenarioTask(crossroads_task.scenario, 0))


def test_exact_checkpoint_bounds_not_gym_approximate_equality(
        crossroads_task, initialized_scenario_model, monkeypatch):
    altered = deepcopy(initialized_scenario_model.observation_space)
    altered["unit_stats"].high[0, 0] += np.float32(0.00001)
    assert altered == initialized_scenario_model.observation_space
    monkeypatch.setattr(initialized_scenario_model,
                        "observation_space", altered)
    with pytest.raises(ValueError, match="spaces"):
        ScenarioPolicy(initialized_scenario_model, crossroads_task)


def test_terminal_opening_reset_cannot_trigger_empty_mask_prediction(
        small_scenario, monkeypatch):
    import random
    payload = small_scenario.model_dump(mode="json")
    payload["hex_data"] = [c for c in payload["hex_data"]
                           if c.get("units") != ["Guard"]]
    payload["reinforcements"][0]["units"].append("Guard")
    payload["reinforcements"][0]["arrival_turn"] = 10
    payload["stacking_limit"] = 2
    payload["objectives"] = [{"coords": [3, 0], "points": 1, "type": "occupy"}]
    task = ScenarioTask(small_scenario.model_validate(payload), 1)
    monkeypatch.setattr(random.Random, "choice", lambda rng, legal: 21)
    env = MaskedScenarioEnv(task)
    with pytest.raises(RuntimeError, match="Reset ended"):
        env.reset(seed=0)
    assert env.game_env.game.get_game_status().state == "completed"
    assert not env.action_masks().any()
