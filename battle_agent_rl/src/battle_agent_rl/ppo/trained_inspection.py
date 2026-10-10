"""Inspect one bounded episode using a model trained in this process."""

from .gym_env import policy_action_mask, policy_observation
from .rollout_inspection import inspect


def inspect_trained_episode(model, seed, step_limit, stream=None):
    """Print an audited, deterministic PPO episode without a checkpoint."""
    def choose_action(transition):
        mask = policy_action_mask(transition)
        action, _ = model.predict(
            policy_observation(transition), action_masks=mask,
            deterministic=True,
        )
        return int(action)

    return inspect(
        seed, step_limit, policy="ppo", stream=stream,
        action_selector=choose_action,
    )
