"""Public contract checks for the independent multi-unit prototype."""

import random

import pytest
import numpy as np

from battle_agent_rl.ppo.multi_unit_environment import MultiUnitEnvironment
from battle_agent_rl.ppo.multi_unit_inspection import audit, inspect
from battle_agent_rl.ppo.multi_unit_scenario import create_multi_unit_game
from battle_agent_rl.ppo.multi_unit_state import joint_plan


@pytest.mark.parametrize("learner_count,opponent_count", [
    (1, 1), (1, 2), (2, 1), (2, 2)])
def test_roster_and_reversed_order(learner_count, opponent_count):
    env = MultiUnitEnvironment(1, learner_count, opponent_count)
    initial = env.reset(4)
    assert len(initial.legal_action_mask) == 162
    assert initial.observation["present"] == [
        1, learner_count == 2, 1, opponent_count == 2]
    assert initial.legal_action_mask[29]
    assert initial.legal_action_mask[128] == (learner_count == 2)
    audit(env, initial)
    if learner_count == 2:
        middle = env.step(128)
        assert middle.observation["pending"] == [True, False]
        assert middle.observation["remaining_cycles"] == [1]
        assert middle.legal_action_mask[29]
        assert not any(middle.legal_action_mask[81:])
        assert not middle.info["combats"]
    final = env.step(29)
    assert final.truncated or final.terminated
    assert not any(final.legal_action_mask)
    assert final.observation["pending"] == [False, False]
    audit(env, final)
    with pytest.raises(RuntimeError):
        env.step(29)


def test_invalid_actions_and_paths_preserve_all_state(monkeypatch):
    env = MultiUnitEnvironment()
    initial = env.reset(5)
    snapshot = env.rng.getstate()
    for action in (True, 162, -1, 0, 1.0, "29"):
        with pytest.raises(ValueError):
            env.step(action)
    board = env.game.get_board()
    monkeypatch.setattr(board, "shortest_path", lambda *args: [])
    with pytest.raises(RuntimeError):
        env.step(29)
    assert env.rng.getstate() == snapshot
    assert env.decision_count == 0
    assert env.game.defensive_fire_log == env.game.combat_log == []
    assert env.pending == [True, True]
    assert env.slots[0].get_coords() == (3, 2)
    assert env._transition(None, (), ()).observation == initial.observation


def test_every_masked_action_routes_and_numpy_integers_work():
    env = MultiUnitEnvironment()
    initial = env.reset(1)
    for action, legal in enumerate(initial.legal_action_mask):
        if legal:
            slot, plan = joint_plan(env.game, env.slots[:2], env.pending,
                                    np.int64(action))
            assert slot == action // 81
            assert plan.path[0].row == env.slots[slot].row
            assert (plan.path[-1].row, plan.path[-1].column) == (
                divmod(action % 81, 9))
    env.step(np.int64(128))


def test_casualty_stack_and_live_flags():
    env = MultiUnitEnvironment()
    env.reset(2)
    board = env.game.get_board()
    board.remove_units([env.slots[0]])
    env.pending = [False, True]
    env.slots[1].set_coords(4, 4)
    state = env._transition(None, (), ())
    assert state.observation["present"][0] == 1
    assert state.observation["alive"][0] == 0
    assert sum(state.observation["positions"][0]) == 0
    assert not any(state.legal_action_mask[:81])
    assert state.observation["positions"][1][40] == 1
    assert state.legal_action_mask[121]
    env.slots[0].set_coords(4, 4)
    board.add_unit(env.slots[0], 4, 4)
    env.pending = [True, True]
    stacked = env._transition(None, (), ())
    assert stacked.observation["positions"][0][40] == 1
    assert stacked.observation["positions"][1][40] == 1
    assert stacked.legal_action_mask[40] and stacked.legal_action_mask[121]
    env.slots[2].spend_defensive_fire(env.learner)
    state = env._transition(None, (), ())
    assert state.observation["fire_spent"][2] == 1
    assert state.observation["defensive_fire_ready"][2] == 0


@pytest.mark.parametrize("order,first_target", [
    ((32, 122), "learner-0"), ((122, 32), "learner-1")])
def test_live_fire_before_joint_combat(order, first_target):
    env = MultiUnitEnvironment()
    env.reset(1)
    for unit, coords in zip(env.slots, ((3, 4), (4, 4), (4, 6),
                                        (8, 8))):
        unit.set_coords(*coords)
    env.rng.random = lambda: 0.99  # A shot with no retreat.
    first = env.step(order[0])
    assert len(first.info["defensive_fire"]) == 1
    assert first.info["defensive_fire"][0].target_unit.unit_id == first_target
    assert first.observation["fire_spent"][2] == 1
    assert first.observation["defensive_fire_ready"][2] == 0
    assert not first.info["combats"]
    assert first.legal_action_mask[order[1]]
    second = env.step(order[1])
    assert not second.info["defensive_fire"]
    assert second.info["combats"]


def test_fire_retreat_keeps_order_spent():
    env = MultiUnitEnvironment()
    env.reset(1)
    for unit, coords in zip(env.slots, ((3, 4), (4, 4), (4, 6),
                                        (8, 8))):
        unit.set_coords(*coords)
    env.rng.random = lambda: 0.0
    transition = env.step(32)
    assert transition.info["defensive_fire"][0].outcome == "retreated"
    assert env.slots[0].get_coords() == (3, 4)
    assert transition.observation["forced_retreat"][0] == 1
    assert transition.observation["pending"] == [False, True]
    assert not any(transition.legal_action_mask[:81])
    assert not transition.info["combats"]


def test_complete_turn_cutoff_and_replay():
    traces = []
    for _ in range(2):
        lines = []
        final = inspect(seed=17, policy="random", cycle_limit=2,
                        output=lines.append)
        traces.append(lines)
        assert final.terminated != final.truncated
        assert final.info["decision_count"] <= 4
        if final.truncated:
            assert final.info["outcome"].state == "in_progress"
    assert traces[0] == traces[1]
    env = MultiUnitEnvironment(1)
    env.reset(3)
    env.step(29)
    final = env.step(128)
    assert final.info["completed_cycles"] == 1
    assert final.truncated
    assert final.reward == 0
    assert env.game.get_current_player() is env.learner
    assert env.reset(3).observation["pending"] == [True, True]


@pytest.mark.parametrize("seed,reward,winner", [
    (0, -1, "Opponent"), (1, 1, "Learner"), (6, 0, None)])
def test_authoritative_core_endings(seed, reward, winner):
    final = inspect(seed=seed, cycle_limit=50, output=lambda line: None)
    assert final.terminated and not final.truncated
    assert final.reward == reward
    assert final.info["outcome"].winner_player_name == winner


def test_reject_unsupported_roster_and_live_partial_budget():
    for count in (0, 3, True):
        with pytest.raises(ValueError):
            create_multi_unit_game(random.Random(1), count, 2)
    env = MultiUnitEnvironment()
    env.reset(1)
    env.slots[0].current_turn_movement_points_remaining = 1
    with pytest.raises(RuntimeError):
        joint_plan(env.game, env.slots[:2], env.pending, 29)


def test_gym_space_and_cpu_masked_policy():
    pytest.importorskip("sb3_contrib")
    from sb3_contrib import MaskablePPO
    from battle_agent_rl.ppo.multi_unit_gym import (
        MaskedMultiUnitEnv, predict_joint_action,
    )
    from battle_agent_rl.ppo.gym_env import MaskedBattleHexesEnv

    gym_env = MaskedMultiUnitEnv(cycle_limit=1)
    obs, _ = gym_env.reset(seed=2)
    assert gym_env.observation_space.contains(obs)
    assert sum(array.size for array in obs.values()) == 355
    model = MaskablePPO("MultiInputPolicy", gym_env, device="cpu",
                        n_steps=4, batch_size=2, seed=2,
                        policy_kwargs={"net_arch": [16, 16]})
    weights = [tensor.clone() for tensor in model.policy.parameters()]
    for mask in (gym_env.action_masks(),
                 gym_env.action_masks() & ([False] * 81 + [True] * 81),
                 gym_env.action_masks() & ([False] * 128 + [True] +
                                           [False] * 33)):
        action = predict_joint_action(model, obs, mask)
        assert mask[action]
    obs, _, _, _, _ = gym_env.step(128)
    assert gym_env.observation_space.contains(obs)
    assert predict_joint_action(model, obs, gym_env.action_masks()) < 81
    for left, right in zip(weights, model.policy.parameters()):
        assert left.equal(right)
    old_env = MaskedBattleHexesEnv()
    old_model = MaskablePPO("MultiInputPolicy", old_env, device="cpu",
                            n_steps=4, batch_size=2)
    with pytest.raises(ValueError, match="Incompatible"):
        predict_joint_action(old_model, obs, gym_env.action_masks())
