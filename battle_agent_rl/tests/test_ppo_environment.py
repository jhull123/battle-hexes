import random

import pytest

from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)
from battle_agent_rl.ppo_environment import PPOTrainingEnvironment


def run_episode(seed, step_limit=50):
    env = PPOTrainingEnvironment(step_limit=step_limit)
    result = env.reset(seed)
    policy = random.Random(seed)
    trajectory = []
    while not (result.terminated or result.truncated):
        actions = [i for i, valid in enumerate(result.legal_action_mask)
                   if valid]
        result = env.step(policy.choice(actions))
        trajectory.append((result.observation, result.info["destination"],
                           result.reward, result.terminated, result.truncated))
    return env, result, trajectory


def test_legal_actions_have_paths_and_invalid_actions_do_not_mutate():
    env = PPOTrainingEnvironment()
    initial = env.reset(10)
    board = env.game.get_board()
    unit = board.get_units_for_player(env.learner)[0]
    for index, valid in enumerate(initial.legal_action_mask):
        if valid:
            start = board.get_hex(*unit.get_coords())
            destination = board.get_hex(index // 5, index % 5)
            assert board.shortest_path(unit, start, destination)
    assert initial.legal_action_mask[10]  # hold
    for action in (-1, 25, 14, 1.5, True):
        with pytest.raises(ValueError):
            env.step(action)
        assert env.step_count == 0
        assert env.game.get_turn_number() == 1
        assert unit.get_coords() == (2, 0)
    assert env.step(10).info["destination"] == (2, 0)


def test_seeded_episodes_and_authoritative_outcomes():
    wins = losses = 0
    for seed in range(100):
        env, result, trajectory = run_episode(seed)
        _, replay, repeated = run_episode(seed)
        assert trajectory == repeated
        assert result.info["step_count"] <= env.step_limit
        assert result.terminated
        assert not result.truncated
        status = env.game.get_game_status()
        assert status == result.info["outcome"]
        assert result.reward == replay.reward
        assert result.reward == (
            1 if status.winner_player_name == env.learner.name else
            -1 if status.winner_player_name is not None else 0
        )
        wins += result.reward == 1
        losses += result.reward == -1
        with pytest.raises(RuntimeError):
            env.step(10)
    assert wins and losses


def test_cutoff_is_not_game_result_and_reset_is_fresh():
    env = PPOTrainingEnvironment(step_limit=1)
    first = env.reset(42)
    old_game = env.game
    old_unit = old_game.get_board().get_units_for_player(env.learner)[0]
    result = env.step(10)
    assert result.truncated and not result.terminated
    assert result.reward == 0
    assert result.info["outcome"].state == "in_progress"
    assert not any(result.legal_action_mask)
    with pytest.raises(RuntimeError):
        env.step(10)
    fresh = env.reset(42)
    assert fresh == first
    assert env.game is not old_game
    assert env.game.get_board() is not old_game.get_board()
    new_unit = env.game.get_board().get_units_for_player(env.learner)[0]
    assert new_unit is not old_unit


def test_observation_exposes_defensive_fire_risk_at_same_positions():
    observations = []
    fire_counts = []
    for eligible in (True, False):
        env = PPOTrainingEnvironment(step_limit=1)
        env.reset(2)
        opponent = env.game.get_board().get_units_for_player(
            env.game.players[1]
        )[0]
        opponent.set_coords(2, 2)
        opponent.ended_last_friendly_turn_with_defensive_fire_eligibility = (
            eligible
        )
        opponent.update_defensive_fire_available(env.learner)

        before = env._transition(None, (), ())
        observations.append(before)
        fire_counts.append(len(env.step(11).info["defensive_fire"]))

    ready, unavailable = observations
    assert ready.observation["occupancy"] == unavailable.observation[
        "occupancy"
    ]
    assert ready.legal_action_mask == unavailable.legal_action_mask
    assert ready.observation["defensive_fire_ready"][12] == 1
    assert unavailable.observation["defensive_fire_ready"][12] == 0
    assert fire_counts == [1, 0]


def test_defensive_fire_and_combat_return_post_resolution_board():
    env = PPOTrainingEnvironment()
    env.reset(2)
    board = env.game.get_board()
    enemy = board.get_units_for_player(env.game.players[1])[0]
    enemy.set_coords(2, 2)
    env.game.set_defensive_fire_settings(
        DefensiveFireSettings(base_probability=1)
    )
    result = env.step(11)  # advance adjacent, then retreat under fire
    assert result.info["defensive_fire"]
    assert result.info["defensive_fire"][0].outcome == "retreat"
    assert result.observation["occupancy"][11] == 0
    for tile in board.hexes:
        unit = board.get_unit_at(tile.row, tile.column)
        expected = 0 if unit is None else (
            1 if env.learner.owns(unit) else -1
        )
        assert result.observation["occupancy"][tile.row * 5 + tile.column] \
            == expected

    env, result, trajectory = run_episode(0)
    assert env.game.combat_log
    assert result.reward == 1
    assert result.info["outcome"].state == "completed"
    assert -1 not in result.observation["occupancy"]
    assert not any(result.legal_action_mask)
