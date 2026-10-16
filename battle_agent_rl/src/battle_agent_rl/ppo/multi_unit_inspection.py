"""Bounded dependency-light, core-audited multi-unit rollout inspection."""

import argparse
import random

from .multi_unit_environment import MultiUnitEnvironment
from .multi_unit_state import joint_mask, slot_observation


def audit(env, transition):
    """Fail fast if the exposed policy inputs disagree with live core state."""
    expected = slot_observation(
        env.game, env.slots, env.pending,
        env.cycle_limit - env.completed_cycles, env.learner)
    mask = joint_mask(env.game, env.slots[:2], env.pending,
                      active=not env.done)
    if (transition.observation != expected
            or transition.legal_action_mask != mask):
        raise AssertionError("Multi-unit inputs differ from core")
    if not env.done and not any(mask):
        raise AssertionError("Active learner has no legal action")


def inspect(seed=0, policy="random", cycle_limit=50, learner_count=2,
            opponent_count=2, output=print):
    env = MultiUnitEnvironment(cycle_limit, learner_count, opponent_count)
    transition = env.reset(seed)
    policy_rng = random.Random(seed)
    for _ in range(2 * cycle_limit):
        audit(env, transition)
        mask = transition.legal_action_mask
        if policy == "random":
            action = policy_rng.choice([index for index, legal in
                                        enumerate(mask) if legal])
        elif policy == "hold":
            slot = next(index for index, pending in
                        enumerate(env.pending) if pending)
            row, column = env.slots[slot].get_coords()
            action = slot * 81 + row * 9 + column
        else:
            raise ValueError("Unknown inspection policy")
        if not mask[action]:
            raise AssertionError("Policy selected an illegal order")
        inputs = transition.observation
        positions = [next((divmod(i, 9) for i, bit in enumerate(row)
                           if bit), None) for row in inputs["positions"]]
        output(f"decision={env.decision_count + 1} cycle="
               f"{env.completed_cycles + 1} positions={positions} "
               f"present={inputs['present']} alive={inputs['alive']} "
               f"pending={inputs['pending']} movement="
               f"{inputs['movement_remaining']} ready="
               f"{inputs['defensive_fire_ready']} fire_eligible="
               f"{inputs['fire_eligible_last_turn']} retreat="
               f"{inputs['forced_retreat']} fire_spent="
               f"{inputs['fire_spent']} remaining="
               f"{inputs['remaining_cycles']} "
               f"legal={[i for i, legal in enumerate(mask) if legal]} "
               f"action={action} slot={action // 81} "
               f"destination={divmod(action % 81, 9)}")
        transition = env.step(action)
        audit(env, transition)
        output(f"fire={transition.info['defensive_fire']} "
               f"combat={transition.info['combats']} "
               f"reward={transition.reward} "
               f"completed_cycles={env.completed_cycles}")
        if transition.terminated or transition.truncated:
            ending = "completed" if transition.terminated else "cutoff"
            output(f"ending={ending} "
                   f"status={transition.info['outcome'].state} "
                   f"winner={transition.info['outcome'].winner_player_name}")
            return transition
    raise AssertionError("Rollout exceeded decision bound")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--policy", choices=("random", "hold"),
                        default="random")
    parser.add_argument("--cycle-limit", type=int, default=50)
    parser.add_argument("--learner-count", type=int, choices=(1, 2), default=2)
    parser.add_argument("--opponent-count", type=int, choices=(1, 2),
                        default=2)
    args = parser.parse_args()
    inspect(**vars(args))


if __name__ == "__main__":
    main()
