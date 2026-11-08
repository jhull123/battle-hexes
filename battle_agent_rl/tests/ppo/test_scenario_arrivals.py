"""Arrivals and automatic empty turns via production environment steps."""

import pytest

from battle_agent_rl.ppo.decision_controller import choose_action
from battle_agent_rl.ppo.scenario_environment import ScenarioEnvironment
from battle_agent_rl.ppo.scenario_task import ScenarioTask

from .scenario_env_helpers import assert_inputs, finish_cycle, hold


@pytest.fixture
def env(crossroads_task):
    result = ScenarioEnvironment(crossroads_task, opponent_policy="hold")
    result.reset(0)
    return result


def test_unblocked_arrivals_stable_stacks_and_core_readiness(env):
    finish_cycle(env)
    transition = finish_cycle(env)
    assert env.game.turn_number == 3
    assert len(transition.info["reinforcements"]) == 1
    arrival = transition.info["reinforcements"][0]
    assert arrival.turn_number == 3 and arrival.outcome == "arrived"
    assert transition.observation["pending"].tolist() == [1] * 5
    assert transition.observation["positions"][3, 16] == 1
    assert transition.observation["positions"][4, 16] == 1
    assert transition.observation["movement_remaining"][3:5].tolist() == [3, 7]
    assert transition.observation["fire_flags"][3:5].tolist() == [
        [1, 0, 0, 0], [1, 0, 0, 0]]
    assert transition.legal_action_mask[988]
    assert transition.legal_action_mask[1312]
    assert len([o for o in transition.info["orders"]
                if o["role"] == "opponent" and o["turn_number"] == 3]) == 6


def test_blocked_entry_retries_only_at_cycle_wrap_not_handoff(env):
    blocker = env.binding.slots[0]
    blocker.set_coords(0, 16)  # Capacity two: cannot fit the two-unit group.
    finish_cycle(env)
    transition = finish_cycle(env)
    assert [e.outcome for e in transition.info["reinforcements"]] == [
        "blocked"]
    assert len(env.game.reinforcements_deployer.game_log) == 1
    assert transition.observation["unit_status"][3:5].tolist() == [0, 0]
    assert not transition.legal_action_mask[972:].any()
    transition = finish_cycle(env)
    assert [e.turn_number for e in transition.info["reinforcements"]] == [4]
    assert [e.outcome for e in transition.info["reinforcements"]] == [
        "blocked"]
    assert transition.observation["reinforcement"].tolist() == [[3, 0, 16, 1]]
    blocker.set_coords(3, 15)
    # Still no arrival during German movement, only on the wrap into five.
    transition = hold(env)
    assert not transition.info["reinforcements"]
    assert not transition.legal_action_mask[972:].any()
    transition = finish_cycle(env)
    assert [e.outcome for e in transition.info["reinforcements"]] == [
        "arrived"]
    assert transition.observation["unit_status"][3:5].tolist() == [1, 1]


@pytest.mark.parametrize("die_roll,statuses", [(1, [2, 2]), (2, [2, 1])])
def test_airborne_attacks_arrivals_before_their_first_order(
        env, die_roll, statuses):
    finish_cycle(env)
    attacker = env.binding.slots[5]
    attacker.set_coords(2, 16)
    for coords in ((0, 16), (1, 16)):
        env.game.board.get_hex(*coords).set_terrain(None)
    env.opponent_policy = "random"

    def select(legal):
        if env.game.turn_number == 3 and attacker.id in env.pending:
            assert 34 in legal  # Airborne local slot 0 -> (1,16).
            return 34
        return choose_action(env.opponent_binding, env.pending,
                             "hold", env.rng)

    env.rng.choice = select
    env.rng.randint = lambda *args: die_roll
    transition = finish_cycle(env)
    assert transition.info["reinforcements"][0].outcome == "arrived"
    assert not transition.info["defensive_fire"]  # Fresh arrivals cannot fire.
    assert (transition.info["combats"][0].player_name
            == env.binding.opponent.name)
    assert transition.info["combats"][0].eliminated_units
    assert transition.observation["unit_status"][3:5].tolist() == statuses
    assert transition.observation["reinforcement"][0, 3] == 2
    assert not transition.legal_action_mask[972:1296].any()
    assert transition.observation["pending"][3:5].tolist() == [
        int(status == 1) for status in statuses]
    if statuses[1] == 1:
        assert transition.observation["movement_remaining"][4] == 7
        assert transition.observation["fire_flags"][4].tolist() == [1, 0, 0, 0]
        assert transition.legal_action_mask[1312]


def test_stale_pending_casualties_are_pruned_before_next_decision(env):
    env.game.board.remove_units(env.binding.slots[:2])
    transition = env.step(765)  # Last on-board German's hold.
    assert transition.info["decision_count"] == 1
    assert not transition.terminated and transition.reward == 0
    assert transition.observation["pending"].tolist() == [0, 0, 1, 0, 0]
    assert_inputs(env, transition)


@pytest.mark.parametrize("cap", [1, 8])
def test_reset_automatically_closes_empty_german_turns(crossroads_task, cap):
    payload = crossroads_task.scenario.model_dump(mode="json")
    initial_ids = set(crossroads_task.spec.learner_ids[:3])
    for cell in payload["hex_data"]:
        cell["units"] = [u for u in (cell.get("units") or [])
                         if u not in initial_ids]
    payload["reinforcements"].append({
        "id": "later-infantry", "units": sorted(initial_ids),
        "arrival_turn": 3,
        "entry_location": {"mode": "fixed", "coords": [0, 0]}})
    payload["stacking_limit"] = 3
    task = ScenarioTask(crossroads_task.scenario.model_validate(payload), 1)
    env = ScenarioEnvironment(task, cap, opponent_policy="hold")
    transition = env.reset(0)
    assert_inputs(env, transition)
    assert transition.info["decision_count"] == 0
    assert not transition.info["combats"]
    assert not transition.terminated and transition.reward == 0
    assert transition.truncated == (cap == 1)
    assert env.game.turn_number == (2 if cap == 1 else 3)
    opponent_turns = [o["turn_number"] for o in transition.info["orders"]]
    assert opponent_turns == [1] * 6 + ([] if cap == 1 else [2] * 6 + [3] * 6)
    if cap == 8:
        assert transition.observation["pending"].tolist() == [1] * 5


def test_all_airborne_eliminated_is_not_a_fabricated_german_win(env):
    env.game.board.remove_units(env.binding.slots[5:])
    transition = finish_cycle(env)
    assert not transition.terminated and transition.reward == 0
    assert len(transition.info["orders"]) == 1  # No empty-side pass actions.
    assert transition.info["core_status"] == "in_progress"
    while not env.done:
        transition = finish_cycle(env)
    assert transition.terminated and transition.reward == 1
    assert transition.info["core_reason"] == "objective_control"
