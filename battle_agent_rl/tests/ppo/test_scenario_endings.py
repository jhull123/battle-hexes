"""Core scores, learner-relative rewards and completion/cutoff ordering."""

import random

import pytest

from battle_agent_rl.ppo.scenario_environment import ScenarioEnvironment
from battle_agent_rl.ppo.scenario_task import ScenarioTask

from .scenario_env_helpers import assert_inputs, finish_cycle, hold


@pytest.mark.parametrize("occupied,reward,scores", [
    (0, 1, [3, 0]), (2, -1, [1, 2])])
def test_crossroads_objective_completion_and_terminal_rewards(
        crossroads_task, occupied, reward, scores):
    env = ScenarioEnvironment(crossroads_task, opponent_policy="hold")
    env.reset(0)
    # Controlled occupation, no adjacency/combat. The remaining objectives are
    # empty and still score for the non-scoring side, not accumulated captures.
    for unit, coords in zip(env.binding.learner_slots[:3],
                            ((0, 0), (0, 2), (0, 4))):
        unit.set_coords(*coords)
    for unit, coords in zip(env.binding.slots[5:],
                            crossroads_task.spec.objective_coords[:occupied]):
        unit.set_coords(*coords)
    rewards = []
    while not env.done:
        transition = hold(env)
        assert_inputs(env, transition)
        rewards.append(transition.reward)
    assert rewards[:-1] == [0] * (len(rewards) - 1)
    assert rewards[-1] == reward
    assert transition.terminated and not transition.truncated
    assert transition.info["core_reason"] == "objective_control"
    assert transition.info["scores"] == scores
    assert env.game.turn_number == 8
    assert transition.observation["remaining_cycles"].tolist() == [1]
    assert env.game.current_phase is None and env.game.current_player is None
    assert transition.info["orders"][-1]["role"] == "learner"
    with pytest.raises(RuntimeError, match="Reset"):
        env.step(69)


def test_cutoff_after_second_seat_before_next_airborne_action(crossroads_task):
    env = ScenarioEnvironment(crossroads_task, 2, opponent_policy="hold")
    env.reset(0)
    finish_cycle(env)
    transition = finish_cycle(env)
    assert transition.truncated and not transition.terminated
    assert transition.reward == 0 and transition.info["outcome"] == "cutoff"
    assert transition.info["core_status"] == "in_progress"
    assert transition.observation["remaining_cycles"].tolist() == [6]
    assert env.game.turn_limit == 8 and env.game.turn_number == 3
    assert env.game.current_player is env.binding.opponent
    assert transition.info["reinforcements"][0].outcome == "arrived"
    assert transition.observation["unit_status"][3:5].tolist() == [1, 1]
    assert [o["role"] for o in transition.info["orders"]] == ["learner"]
    assert not env.action_masks().any()
    with pytest.raises(RuntimeError, match="Reset"):
        env.step(988)


@pytest.mark.parametrize("seat", [0, 1])
def test_unregistered_rectangular_scenario_both_seats_and_draw(
        small_scenario, tmp_path, seat):
    scenario = small_scenario.model_copy(update={"id": "editor-environment"})
    (tmp_path / "editor-environment.json").write_text(
        scenario.model_dump_json(), encoding="utf-8")
    task = ScenarioTask.load("editor-environment", learner_seat=seat,
                             scenario_dir=tmp_path)
    env = ScenarioEnvironment(task, opponent_policy="hold")
    transition = env.reset(21)
    assert_inputs(env, transition)
    env.game.board.get_unit_by_id("Scout").set_coords(3, 1)
    arrivals = []
    while not env.done:
        transition = hold(env)
        assert_inputs(env, transition)
        arrivals.extend(transition.info["reinforcements"])
    assert task.spec.board_size == (5, 7)
    assert len(arrivals) == 2 and all(e.outcome == "arrived" for e in arrivals)
    assert transition.info["decision_count"] == 7
    assert transition.terminated and not transition.truncated
    assert transition.info["outcome"] == "draw" and transition.reward == 0
    assert transition.info["scores"] == [1, 1]
    assert env.game.turn_number == 4


def test_completion_during_opponent_turn_stops_before_next_prediction(
        small_scenario):
    scenario = small_scenario.model_copy(update={
        "objectives": [], "victory": None})
    env = ScenarioEnvironment(ScenarioTask(scenario, 1),
                              opponent_policy="hold")
    env.reset(0)
    scout = env.game.board.get_unit_by_id("Scout")
    guard = env.game.board.get_unit_by_id("Guard")
    scout.set_coords(3, 2)
    guard.set_coords(3, 4)
    for group in env.game.reinforcements_deployer.groups:
        group.entered = True  # Controlled fixture: reserves already lost.
    env.opponent_policy = "random"
    env.rng.choice = lambda legal: 24  # Scout -> (3,3), after German hold.
    env.rng.random = lambda: .99
    env.rng.randint = lambda *args: 1  # Core 2:1 defender eliminated.
    transition = hold(env)
    assert transition.terminated and not transition.truncated
    assert transition.reward == -1 and transition.info["outcome"] == "loss"
    assert transition.info["core_reason"] == "unit_elimination"
    assert transition.info["decision_count"] == 1
    assert [o["role"] for o in transition.info["orders"]] == [
        "learner", "opponent"]
    assert len(transition.info["combats"]) == 1
    assert_inputs(env, transition)


def test_completion_during_opening_movement_returns_terminal_reset(
        small_scenario, monkeypatch):
    payload = small_scenario.model_dump(mode="json")
    payload["hex_data"] = [c for c in payload["hex_data"]
                           if c.get("units") != ["Guard"]]
    payload["reinforcements"][0]["units"].append("Guard")
    payload["reinforcements"][0]["arrival_turn"] = 10  # Beyond the horizon.
    payload["stacking_limit"] = 2
    payload["objectives"] = [{"coords": [3, 0], "points": 1, "type": "occupy"}]
    task = ScenarioTask(small_scenario.model_validate(payload), 1)

    def choose(rng, legal):
        assert 21 in legal
        return 21  # Red Scout occupies the only objective during movement.

    monkeypatch.setattr(random.Random, "choice", choose)
    env = ScenarioEnvironment(task, cycle_limit=1)
    transition = env.reset(0)
    assert transition.terminated and not transition.truncated
    assert transition.reward == -1 and transition.info["decision_count"] == 0
    assert transition.info["core_reason"] == "unit_elimination"
    assert transition.info["scores"] == [0, 1]
    assert len(transition.info["orders"]) == 1
    assert not transition.info["combats"]
    assert_inputs(env, transition)
