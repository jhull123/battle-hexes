"""Scoring after core combat, before final evaluation, and current control."""

from battle_agent_rl.ppo.scenario_environment import ScenarioEnvironment
from battle_agent_rl.ppo.scenario_task import ScenarioTask

from .scenario_env_helpers import assert_inputs, hold


def test_post_combat_control_decides_completion_at_the_external_bound(
        small_scenario):
    payload = small_scenario.model_dump(mode="json")
    payload["turn_limit"] = 1
    payload["objectives"] = [{"coords": [3, 3], "points": 1, "type": "occupy"}]
    task = ScenarioTask(small_scenario.model_validate(payload), 1)
    env = ScenarioEnvironment(task, 1, opponent_policy="hold")
    env.reset(0)
    scout = env.game.board.get_unit_by_id("Scout")
    guard = env.game.board.get_unit_by_id("Guard")
    scout.set_coords(3, 3)
    guard.set_coords(3, 4)
    env.rng.randint = lambda *args: 1  # Core 2:1 -> defender eliminated.
    transition = hold(env)
    assert len(transition.info["combats"]) == 1
    assert transition.info["combats"][0].eliminated_units == ("Scout",)
    assert transition.info["scores"] == [1, 0]  # The objective is now empty.
    assert transition.observation["objective_control"].tolist() == [0]
    assert transition.terminated and not transition.truncated
    assert transition.reward == 1 and transition.info["outcome"] == "win"
    assert transition.info["core_reason"] == "objective_control"
    assert_inputs(env, transition)


def test_scores_are_current_control_not_capture_accumulation(crossroads_task):
    env = ScenarioEnvironment(crossroads_task, opponent_policy="hold")
    env.reset(0)
    airborne = env.binding.slots[5]
    airborne.set_coords(2, 3)
    env.step(69)
    env.step(401)
    captured = env.step(765)
    assert captured.info["scores"] == [2, 1]
    airborne.set_coords(12, 11)
    env.step(69)
    env.step(401)
    vacated = env.step(765)
    assert vacated.info["scores"] == [3, 0]
    assert_inputs(env, vacated)
