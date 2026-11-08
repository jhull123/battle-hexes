"""Explicit human commands share environment conversion and core semantics."""

import json

import pytest

from battle_agent_rl.ppo.decision_controller import choose_action
from battle_agent_rl.ppo.scenario_environment import ScenarioEnvironment
from battle_agent_rl.ppo.scenario_human import console_orders, play
from battle_agent_rl.ppo.scenario_policy import ScenarioPolicy


def test_human_first_awaits_orders_and_matches_substitute_through_completion(
        crossroads_task, initialized_scenario_model, monkeypatch):
    human_turns = []
    predictions = []
    original = initialized_scenario_model.predict

    def predict(*args, **kwargs):
        assert human_turns  # No opening learner-first prediction.
        predictions.append(len(human_turns))
        return original(*args, **kwargs)

    monkeypatch.setattr(initialized_scenario_model, "predict", predict)

    def human(binding, pending):
        assert binding.game.current_player is binding.game.players[0]
        assert binding.game.current_phase == "movement"
        human_turns.append(binding.game.turn_number)
        return choose_action(binding, pending, "hold", None)

    lines = []
    final = play(crossroads_task, initialized_scenario_model, human,
                 seed=1000, output=lines.append)
    records = [json.loads(line) for line in lines]
    assert final.terminated and final.info["core_status"] == "completed"
    assert predictions[0] == 6
    assert sorted(set(human_turns)) == list(range(1, 9))
    assert len(predictions) == final.info["decision_count"]
    # Same seed, masks, frozen choices, orders/events/scores/endings as the
    # production non-learning substitute (including arrival on turn 3).
    env = ScenarioEnvironment(crossroads_task, opponent_policy="hold")
    policy = ScenarioPolicy(initialized_scenario_model, crossroads_task)
    result = env.reset(1000)
    expected = []
    while True:
        expected.append(json.loads(json.dumps(
            {**result.info, "reward": result.reward,
             "terminated": result.terminated, "truncated": result.truncated},
            default=lambda event: event.__dict__)))
        if env.done:
            break
        result = env.step(policy.predict(result.observation,
                                         result.legal_action_mask))
    assert [{k: v for k, v in r.items() if k != "kind"}
            for r in records] == expected


def test_console_waits_reprompts_and_eof_does_not_auto_hold(
        crossroads_task, initialized_scenario_model, monkeypatch):
    monkeypatch.setattr(initialized_scenario_model, "predict",
                        lambda *a, **k: pytest.fail("PPO acted before human"))
    prompts = []
    outputs = []
    answers = iter(["not-an-order", "1944", "227"])

    def read(prompt):
        prompts.append(prompt)
        return next(answers)

    supplied = []

    def human(binding, pending):
        if not supplied:
            supplied.append(console_orders(binding, pending, read=read,
                                           output=outputs.append))
            return supplied[-1]
        # No input for the next human order: abort, never replace with hold.
        raise EOFError("Awaiting explicit next human order")

    with pytest.raises(EOFError):
        play(crossroads_task, initialized_scenario_model, human,
             output=outputs.append)
    assert supplied == [227] and len(prompts) == 3
    assert json.loads(outputs[0])["kind"] == "human_prompt"


def test_human_driver_cutoff_does_not_request_next_cycle_orders(
        crossroads_task, initialized_scenario_model):
    human_turns = []

    def human(binding, pending):
        human_turns.append(binding.game.turn_number)
        return choose_action(binding, pending, "hold", None)

    result = play(crossroads_task, initialized_scenario_model, human,
                  seed=0, cycle_limit=2, output=lambda _: None)
    assert result.truncated and not result.terminated
    assert result.info["core_status"] == "in_progress"
    assert max(human_turns) == 2
    assert result.observation["remaining_cycles"].tolist() == [6]
