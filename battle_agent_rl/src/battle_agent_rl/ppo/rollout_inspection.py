"""Inspect and audit one seeded training-environment episode."""

import argparse
import os
import random
import sys

from .environment import PPOTrainingEnvironment
from .inspection_audit import verify_transition
from .inspection_view import InspectionView


def _select_action(transition, policy, rng):
    legal = [i for i, allowed in enumerate(transition.legal_action_mask)
             if allowed]
    if not legal:
        raise ValueError("active decision has no legal actions")
    if policy == "random":
        return rng.choice(legal)
    action = next((i for i in legal
                   if transition.observation["occupancy"][i] == 1), None)
    if action is None:
        raise ValueError("hold action unavailable")
    return action


def _step(env, transition, step, policy, rng, view):
    action = _select_action(transition, policy, rng)
    view.state("pre-action decision", transition, env.COLUMNS,
               selected=action)
    destination = divmod(action, env.COLUMNS)
    view.line(view.emphasis(
        f"action: index={action} destination={destination}", "1;33"))
    result = env.step(action)
    if result.info["destination"] != destination:
        raise ValueError("destination mismatch")
    verify_transition(env, result, step)
    view.result(result)
    ended = result.terminated or result.truncated
    view.state("final state" if ended else "next decision", result,
               env.COLUMNS)
    return result


def inspect(seed, step_limit, policy="random", expect_ending=None,
            stream=None, color=None,
            environment_factory=PPOTrainingEnvironment):
    stream = stream if stream is not None else sys.stdout
    if color is None:
        color = stream.isatty() and "NO_COLOR" not in os.environ
    view = InspectionView(stream, color)
    env = environment_factory(step_limit=step_limit)
    rng = random.Random(seed)
    step = 0
    try:
        transition = env.reset(seed)
        verify_transition(env, transition, step)
        view.line(f"episode: seed={seed} step_limit={step_limit} "
                  f"policy={policy}")
        view.state("initial decision", transition, env.COLUMNS)
        while not (transition.terminated or transition.truncated):
            step += 1
            transition = _step(env, transition, step, policy, rng, view)
        view.summary(transition, env.learner.name)
        ending = "completed" if transition.terminated else "cutoff"
        if expect_ending is not None and ending != expect_ending:
            raise ValueError(f"expected {expect_ending} ending, got {ending}")
        return transition
    except Exception as error:
        if str(error).startswith(f"step {step}:"):
            raise
        raise ValueError(f"step {step}: {error}") from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--step-limit", type=int, default=50)
    parser.add_argument("--policy", choices=("random", "hold"),
                        default="random")
    parser.add_argument("--expect-ending", choices=("completed", "cutoff"))
    args = parser.parse_args(argv)
    if args.step_limit < 1:
        parser.error("--step-limit must be positive")
    try:
        inspect(args.seed, args.step_limit, args.policy, args.expect_ending)
    except Exception as error:
        print(f"rollout inspection failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
