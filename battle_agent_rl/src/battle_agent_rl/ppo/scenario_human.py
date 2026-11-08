"""Local explicit human orders versus a frozen, task-bound masked policy."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from .decision_actions import action_mask, action_plan
from .decision_controller import choose_action
from .scenario_environment import ScenarioEnvironment
from .scenario_task import ScenarioTask


def console_orders(binding, pending, *, read=input, output=print):
    """Wait for an explicit index. EOF/interrupt abort; never auto-hold."""
    output(json.dumps({
        "kind": "human_prompt", "turn": binding.game.turn_number,
        "slot_ids": binding.spec.learner_ids,
        "positions": [u.get_coords() for u in binding.learner_slots],
        "legal": np.flatnonzero(action_mask(binding, pending)).tolist(),
    }))
    while True:
        text = read("Human order (unit-slot/destination action index): ")
        try:
            action = int(text)
            action_plan(binding, pending, action)
            return action
        except (ValueError, RuntimeError) as error:
            output(f"Invalid order: {error}")


def play(task, model, human_orders, *, seed=0, cycle_limit=None, output=print):
    from .scenario_policy import ScenarioPolicy

    policy = ScenarioPolicy(model, task)
    env = ScenarioEnvironment(task, cycle_limit, human_orders)

    def emit(kind, transition):
        output(json.dumps({"kind": kind, **transition.info,
                           "reward": transition.reward,
                           "terminated": transition.terminated,
                           "truncated": transition.truncated},
                          default=asdict, sort_keys=True))

    # reset blocks on first-seat human orders before any policy call.
    transition = env.reset(seed)
    emit("reset", transition)
    while not env.done:
        action = policy.predict(transition.observation,
                                transition.legal_action_mask)
        transition = env.step(action)
        emit("transition", transition)
    return transition


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--scenario-dir", type=Path)
    parser.add_argument("--learner-seat", required=True, type=int,
                        choices=(0, 1))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--cycle-limit", type=int)
    parser.add_argument("--scripted-human", choices=("hold",),
                        help="Explicit validation substitute, not interactive")
    args = parser.parse_args()
    task = ScenarioTask.load(args.scenario, learner_seat=args.learner_seat,
                             scenario_dir=args.scenario_dir)
    from .playable_artifact import load_model
    model, _ = load_model(args.run_dir, task=task)

    def scripted_orders(binding, pending):
        return choose_action(binding, pending, "hold", None)

    orders = scripted_orders if args.scripted_human else console_orders
    play(task, model, orders, seed=args.seed, cycle_limit=args.cycle_limit)


if __name__ == "__main__":
    main()
