"""Repeatable non-learning inspection; no Gym, Torch or trainer is imported."""

import argparse
from dataclasses import asdict
import json
import hashlib
import platform
import random
from pathlib import Path

import numpy as np

from .decision_audit import audit_decision
from .decision_controller import choose_action
from .scenario_environment import ScenarioEnvironment
from .scenario_task import ScenarioTask


def _state_record(env, transition):
    inputs = transition.observation
    return {
        "turn": env.game.turn_number,
        "positions": [u.get_coords() for u in env.binding.slots],
        **{key: inputs[key].tolist() for key in (
            "unit_status", "pending", "movement_remaining", "fire_flags",
            "scores", "objective_control", "reinforcement",
            "remaining_cycles")},
        "legal": np.flatnonzero(transition.legal_action_mask).tolist(),
    }


def _result_record(transition):
    info = transition.info
    return {
        **{key: info[key] for key in (
            "decision_count", "orders", "core_status", "core_reason",
            "winner", "outcome", "scores")},
        **{key: [asdict(event) for event in info[key]] for key in (
            "defensive_fire", "combats", "reinforcements")},
        "reward": transition.reward, "terminated": transition.terminated,
        "truncated": transition.truncated,
    }


def _configuration_record(env, seed, policy_seed, policy):
    task = env.task
    snapshot = json.dumps(task.scenario.model_dump(mode="json"),
                          sort_keys=True)
    return {
        "scenario": task.scenario_id,
        "scenario_version": task.scenario_version,
        "contract": task.contract, "learner_seat": task.learner_seat,
        "slot_ids": task.spec.slot_ids, "seed": seed,
        "policy_seed": policy_seed, "policy": policy,
        "opponent_policy": env.opponent_policy, "cycle_limit": env.cycle_limit,
        "scenario_horizon": task.spec.turn_limit,
        "scenario_digest": hashlib.sha256(snapshot.encode()).hexdigest(),
        "python": platform.python_version(), "numpy": np.__version__,
    }


def inspect(task, seed=0, policy="random", opponent_policy="random",
            cycle_limit=None, policy_seed=None, output=print):
    """Print deterministic JSON lines with provenance and live events."""
    if policy not in ("random", "hold"):
        raise ValueError("policy must be random or hold")
    policy_seed = seed if policy_seed is None else policy_seed
    learner_rng = random.Random(policy_seed)
    env = ScenarioEnvironment(task, cycle_limit, opponent_policy)

    def emit(kind, **values):
        output(json.dumps({"kind": kind, **values}, sort_keys=True))

    emit("configuration", **_configuration_record(
        env, seed, policy_seed, policy))
    transition = env.reset(seed)
    audit_decision(env, transition)
    emit("reset", core_player_order=[p.name for p in env.game.players],
         **_result_record(transition))
    bound = len(task.spec.learner_ids) * env.cycle_limit
    while not env.done:
        if env.decision_count >= bound:
            raise AssertionError("Rollout exceeded derived order bound")
        action = choose_action(env.binding, env.pending, policy, learner_rng)
        emit("decision", decision=env.decision_count + 1, action=action,
             **_state_record(env, transition))
        transition = env.step(action)
        audit_decision(env, transition)
        emit("transition", **_result_record(transition))
    emit("ending", **{**_state_record(env, transition),
                      **_result_record(transition)})
    return transition


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--scenario-dir", type=Path)
    parser.add_argument("--learner-seat", type=int, choices=(0, 1),
                        required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--policy-seed", type=int)
    parser.add_argument("--policy", choices=("random", "hold"),
                        default="random")
    parser.add_argument("--opponent-policy", choices=("random", "hold"),
                        default="random")
    parser.add_argument("--cycle-limit", type=int)
    parser.add_argument("--expect-ending", choices=("completed", "cutoff"))
    args = parser.parse_args()
    task = ScenarioTask.load(args.scenario, learner_seat=args.learner_seat,
                             scenario_dir=args.scenario_dir)
    final = inspect(task, args.seed, args.policy, args.opponent_policy,
                    args.cycle_limit, args.policy_seed)
    ending = "completed" if final.terminated else "cutoff"
    if args.expect_ending and ending != args.expect_ending:
        parser.exit(1, f"Expected {args.expect_ending}, got {ending}\n")


if __name__ == "__main__":
    main()
