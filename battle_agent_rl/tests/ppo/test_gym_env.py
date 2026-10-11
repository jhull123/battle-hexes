import numpy as np
import pytest

from battle_agent_rl.ppo.gym_env import MaskedBattleHexesEnv


def test_spaces_masks_and_invalid_actions_preserve_game():
    env = MaskedBattleHexesEnv(step_limit=10)
    with pytest.raises(RuntimeError):
        env.action_masks()
    obs, info = env.reset(seed=10)
    assert info["episode_seed"] == 10
    assert env.observation_space.contains(obs)
    assert obs["occupancy"].dtype == np.int8
    assert obs["defensive_fire_ready"].dtype == np.int8
    assert obs["remaining_steps"].dtype == np.int32
    assert obs["remaining_steps"].tolist() == [10]
    mask = env.action_masks()
    assert mask.dtype == np.bool_ and mask.shape == (25,)
    assert mask.tolist() == list(env.game_env._transition(
        None, (), ()
    ).legal_action_mask)
    mask[:] = False
    assert env.action_masks()[10]
    for invalid in (-1, 25, 14, 1.0, True, np.array([10])):
        with pytest.raises(ValueError):
            env.step(invalid)
        assert env.game_env.step_count == 0
        assert env.game_env.game.get_turn_number() == 1
    obs, reward, terminated, truncated, info = env.step(np.int64(10))
    assert env.observation_space.contains(obs)
    assert info["destination"] == (2, 0)
    assert not (terminated or truncated)
    assert reward == 0.0
    assert env.action_masks().tolist() == list(env.game_env._transition(
        None, (), ()
    ).legal_action_mask)


def test_cutoff_auto_reset_seed_sequence_and_fresh_observations():
    env = MaskedBattleHexesEnv(step_limit=1)
    first, info = env.reset(seed=42)
    assert info["episode_seed"] == 42
    obs, reward, terminated, truncated, info = env.step(10)
    assert env.observation_space.contains(obs)
    assert obs["remaining_steps"].tolist() == [0]
    assert (reward, terminated, truncated) == (0.0, False, True)
    assert info["outcome"].state == "in_progress"
    assert info["ppo_episode"] == {
        "outcome": "cutoff", "length": 1, "return": 0, "seed": 42,
    }
    assert not env.action_masks().any()
    with pytest.raises(RuntimeError):
        env.step(10)
    next_obs, info = env.reset()
    assert info["episode_seed"] == 43
    assert env.observation_space.contains(next_obs)
    assert env.action_masks().any()
    next_obs["occupancy"][:] = -1
    assert env.game_env._transition(None, (), ()).observation[
        "occupancy"
    ][10] == 1
    replay, info = env.reset(seed=42)
    assert info["episode_seed"] == 42
    assert all(np.array_equal(first[key], replay[key]) for key in first)


def test_completion_summary_matches_underlying_transition():
    env = MaskedBattleHexesEnv()
    obs, _ = env.reset(seed=0)
    import random
    policy = random.Random(0)
    while True:
        legal = np.flatnonzero(env.action_masks())
        obs, reward, terminated, truncated, info = env.step(
            int(policy.choice(legal))
        )
        assert env.observation_space.contains(obs)
        if terminated or truncated:
            break
    assert terminated and not truncated
    assert not env.action_masks().any()
    assert info["ppo_episode"] == {
        "outcome": "win", "length": env.game_env.step_count,
        "return": 1, "seed": 0,
    }
    assert reward == 1.0
    # A core win on the limit step takes precedence over time truncation.
    limit = env.game_env.step_count
    at_limit = MaskedBattleHexesEnv(step_limit=limit)
    at_limit.reset(seed=0)
    policy = random.Random(0)
    for _ in range(limit):
        action = policy.choice(np.flatnonzero(at_limit.action_masks()))
        final_obs, final_reward, done, cutoff, final_info = at_limit.step(
            int(action)
        )
    assert done and not cutoff
    assert final_reward == 1.0
    assert final_obs["remaining_steps"].tolist() == [0]
    assert final_info["ppo_episode"]["outcome"] == "win"
