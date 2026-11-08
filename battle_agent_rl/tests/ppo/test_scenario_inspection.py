"""Non-learning replay, actionable inspection and fail-fast live audits."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from battle_agent_rl.ppo.decision_audit import audit_decision
from battle_agent_rl.ppo.scenario_environment import ScenarioEnvironment
from battle_agent_rl.ppo.scenario_inspection import inspect


@pytest.mark.parametrize("policy,opponent,cap", [
    ("hold", "hold", None), ("random", "random", None),
    ("hold", "random", 2)])
def test_seeded_action_event_state_replay(
        crossroads_task, policy, opponent, cap):
    traces = []
    for _ in range(2):
        lines = []
        final = inspect(crossroads_task, seed=17, policy=policy,
                        opponent_policy=opponent, cycle_limit=cap,
                        output=lines.append)
        traces.append(lines)
        assert final.terminated == (cap is None)
        assert final.truncated == (cap is not None)
    assert traces[0] == traces[1]
    records = [json.loads(line) for line in traces[0]]
    config = records[0]
    assert config["seed"] == config["policy_seed"] == 17
    assert config["scenario_horizon"] == 8
    assert config["learner_seat"] == 1 and config["scenario_digest"]
    assert records[1]["kind"] == "reset"
    assert len(records[1]["orders"]) == 6
    assert all(o["action"] < 1944 for o in records[1]["orders"])
    endings = records[-1]
    assert endings["kind"] == "ending"
    assert not endings["legal"] and endings["pending"] == [0] * 5
    arrivals = [e for r in records[:-1] for e in r.get("reinforcements", [])]
    assert len(arrivals) == 1 and arrivals[0]["turn_number"] == 3
    if cap is None:
        assert endings["core_reason"] == "objective_control"
    else:
        assert endings["remaining_cycles"] == [6]


def test_inspector_audit_detects_stale_live_inputs(crossroads_task):
    env = ScenarioEnvironment(crossroads_task, opponent_policy="hold")
    transition = env.reset(0)
    transition.observation["fire_flags"][0, 0] = 0
    with pytest.raises(AssertionError):
        audit_decision(env, transition)


def test_cli_without_gym_or_trainer_and_expected_ending():
    root = Path(__file__).resolve().parents[3]
    script = """
import builtins
import runpy
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('gymnasium', 'torch', 'sb3_contrib',
                              'stable_baselines3'):
        raise AssertionError('Inspection imported a trainer dependency')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
runpy.run_module('battle_agent_rl.ppo.scenario_inspection',
                 run_name='__main__')
"""
    command = [sys.executable, "-c", script, "--scenario", "d_day_crossroads",
               "--learner-seat", "1", "--seed", "0", "--policy", "hold",
               "--opponent-policy", "hold", "--cycle-limit", "1",
               "--expect-ending", "cutoff"]
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join([
        str(root / "battle_agent_rl/src"),
        str(root / "battle_hexes_core/src")])}
    result = subprocess.run(command, cwd=root, env=environment,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout.splitlines()[-1])["outcome"] == "cutoff"
    command[-1] = "completed"
    result = subprocess.run(command, cwd=root, env=environment,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 1
