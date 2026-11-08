"""08b production reset/step: live orders, core phases and invalid requests."""

import pickle
import random

import numpy as np
import pytest

from battle_agent_rl.ppo.decision_actions import action_plan
from battle_agent_rl.ppo.scenario_environment import ScenarioEnvironment
from battle_agent_rl.ppo.scenario_task import ScenarioTask

from .scenario_env_helpers import assert_inputs, hold


@pytest.fixture
def env(crossroads_task):
    result = ScenarioEnvironment(crossroads_task, opponent_policy="hold")
    result.reset(17)
    return result


def test_reset_opens_with_core_first_seat_and_no_learner_orders(env):
    previous = env.game
    transition = env.reset(17)
    assert env.game is not previous
    assert env.game.players[0] is env.binding.opponent
    assert env.game.current_player is env.game.players[1]
    assert transition.info["decision_count"] == 0
    assert [o["unit_id"] for o in transition.info["orders"]] == [
        f"Airborne Inf. {letter}" for letter in "ABCDEF"]
    assert [o["action"] for o in transition.info["orders"]] == [
        227, 547, 934, 1261, 1584, 1915]
    assert all(o["role"] == "opponent" for o in transition.info["orders"])
    assert transition.observation["remaining_cycles"].tolist() == [8]
    assert transition.observation["scores"].tolist() == [3, 0]
    assert transition.observation["pending"].tolist() == [1, 1, 1, 0, 0]
    assert_inputs(env, transition)


@pytest.mark.parametrize("first,second", [(69, 401), (401, 69), (765, 69)])
def test_any_pending_unit_and_hold_consumption(env, first, second):
    transition = env.step(np.array(first))
    assert transition.info["decision_count"] == 1
    assert not transition.info["combats"]
    assert len(transition.info["orders"]) == 1
    slot = first // 324
    assert not transition.legal_action_mask[slot * 324:(slot + 1) * 324].any()
    assert transition.legal_action_mask[second]
    assert_inputs(env, transition)
    while env.game.turn_number == 1:
        transition = hold(env)
    assert [o["role"] for o in transition.info["orders"]] == [
        "learner"] + ["opponent"] * 6
    assert transition.observation["pending"].tolist() == [1, 1, 1, 0, 0]
    assert_inputs(env, transition)


def test_invalid_requests_do_not_mutate_any_environment_state(
        env, monkeypatch):
    env.step(401)

    def snapshot():
        return pickle.dumps((env.game, env.pending, env.rng.getstate(),
                             env.decision_count, env.done, env._turn_key))

    before = snapshot()
    for action in (True, False, -1, 1620, 69.0, np.array([69]), 401, 988, 764):
        with pytest.raises(ValueError):
            env.step(action)
        assert snapshot() == before
    monkeypatch.setattr(type(env.game.board), "shortest_path",
                        lambda *args: [])
    before = snapshot()
    with pytest.raises(RuntimeError, match="route"):
        env.step(69)
    assert snapshot() == before
    env.binding.slots[0].current_turn_movement_points_remaining = 1
    before = snapshot()
    with pytest.raises(RuntimeError, match="spent"):
        env.step(69)
    assert snapshot() == before


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("roll", [0.0, 0.99])
def test_live_fire_retreat_and_reversed_order_before_combat(
        env, reverse, roll):
    # Two Germans approach one ready Airborne defender. All other units are
    # distant; the first mover takes the one available shot.
    a, b, _, _, _, defender = env.binding.slots[:6]
    a.set_coords(3, 4)
    b.set_coords(4, 4)
    defender.set_coords(4, 6)
    env.rng.random = lambda: roll
    first, second = ((401, 59) if reverse else (59, 401))
    mover = b if reverse else a
    transition = env.step(first)
    assert len(transition.info["defensive_fire"]) == 1
    shot = transition.info["defensive_fire"][0]
    assert shot.target_unit.unit_id == mover.id
    assert shot.outcome == ("retreated" if roll == 0 else "noEffect")
    assert mover.id not in env.pending
    assert not transition.info["combats"]
    assert transition.observation["fire_flags"][5, 3] == 1
    assert transition.observation["fire_flags"][5, 0] == 0
    assert transition.observation["fire_flags"][int(reverse), 2] == (roll == 0)
    assert_inputs(env, transition)
    transition = env.step(second)
    assert not transition.info["defensive_fire"]
    assert not transition.info["combats"]  # Feldwache still has its hold.
    assert_inputs(env, transition)
    transition = env.step(765)
    # Applicable battles are core events, once in the German turn and then at
    # most once in the following Airborne turn, never per held unit.
    assert transition.info["combats"]
    sides = [e.player_name for e in transition.info["combats"]]
    assert sides.count(env.learner.name) == 1
    assert sides.count(env.binding.opponent.name) <= 1
    assert_inputs(env, transition)


def test_eliminated_mover_still_consumes_its_order(env):
    mover, _, _, _, _, defender = env.binding.slots[:6]
    mover.set_coords(0, 2)
    defender.set_coords(1, 1)
    env.rng.random = lambda: 0.0
    transition = env.step(1)  # (0,1): the fire retreat would leave the board.
    assert transition.info["defensive_fire"][0].outcome == "eliminated"
    assert transition.observation["unit_status"][0] == 2
    assert mover.id not in env.pending
    assert not transition.legal_action_mask[:324].any()
    assert not transition.terminated and transition.reward == 0
    assert_inputs(env, transition)


def test_feldwache_only_holds_and_core_paths_match_every_mask_bit(env):
    mask = env.action_masks()
    assert np.flatnonzero(mask[648:972]).tolist() == [117]
    for action in np.flatnonzero(mask):
        slot, plan = action_plan(env.binding, env.pending, action)
        assert plan.unit is env.binding.slots[slot]
        assert (plan.path[-1].row, plan.path[-1].column) == divmod(
            int(action) % 324, 18)


@pytest.mark.parametrize("limit", [0, 9, True, 1.5])
def test_cap_validation(crossroads_task, limit):
    with pytest.raises(ValueError, match="cycle_limit"):
        ScenarioEnvironment(crossroads_task, cycle_limit=limit)


def test_reset_aggregates_opening_live_fire_and_combat(
        small_scenario, monkeypatch):
    payload = small_scenario.model_dump(mode="json")
    payload["hex_data"][1]["coords"] = [2, 2]  # Blue Guard.
    task = ScenarioTask(small_scenario.model_validate(payload), 1)

    def select(rng, legal):
        assert 15 in legal
        return 15  # Red Scout -> (2,1), entering defensive fire.

    monkeypatch.setattr(random.Random, "choice", select)
    monkeypatch.setattr(random.Random, "random", lambda rng: .99)
    monkeypatch.setattr(random.Random, "randint", lambda *args: 3)
    env = ScenarioEnvironment(task)
    transition = env.reset(0)
    assert len(transition.info["defensive_fire"]) == 1
    assert transition.info["defensive_fire"][0].target_unit.unit_id == "Scout"
    assert len(transition.info["combats"]) == 1
    assert (transition.info["combats"][0].player_name
            == env.binding.opponent.name)
    assert transition.info["decision_count"] == 0
    assert_inputs(env, transition)
