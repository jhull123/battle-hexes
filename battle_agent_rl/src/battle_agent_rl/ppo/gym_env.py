"""Gymnasium policy-input adapter for the fixed Battle Hexes environment."""

import gymnasium as gym
import numpy as np

from .environment import PPOTrainingEnvironment


def policy_observation(transition):
    """Encode the current core transition for training or prediction."""
    data = transition.observation
    return {
        "occupancy": np.array(data["occupancy"], dtype=np.int8),
        "defensive_fire_ready": np.array(
            data["defensive_fire_ready"], dtype=np.int8
        ),
        "remaining_steps": np.array(
            [data["remaining_steps"]], dtype=np.int32
        ),
    }


def policy_action_mask(transition):
    """Return a fresh mask from the same current transition."""
    return np.array(transition.legal_action_mask, dtype=np.bool_)


class MaskedBattleHexesEnv(gym.Env):
    """One learner decision per step; core environment owns all transitions."""

    metadata = {"render_modes": []}

    def __init__(self, step_limit=50, training_seed=0):
        super().__init__()
        self.game_env = PPOTrainingEnvironment(step_limit=step_limit)
        self.observation_space = gym.spaces.Dict({
            "occupancy": gym.spaces.Box(-1, 1, (25,), dtype=np.int8),
            "defensive_fire_ready": gym.spaces.MultiBinary(25),
            "remaining_steps": gym.spaces.Box(
                0, step_limit, (1,), dtype=np.int32
            ),
        })
        self.action_space = gym.spaces.Discrete(25)
        self._next_seed = training_seed
        self._transition = None
        self._episode_return = 0
        self._episode_seed = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._next_seed = seed
            self.action_space.seed(seed)
        episode_seed = self._next_seed
        self._next_seed += 1
        self._episode_seed = episode_seed
        self._transition = self.game_env.reset(episode_seed)
        self._episode_return = 0
        return policy_observation(self._transition), {
            **self._transition.info, "episode_seed": episode_seed,
        }

    def step(self, action):
        if self._transition is None or self.game_env.done:
            raise RuntimeError("Reset the environment before stepping")
        if isinstance(action, np.ndarray) and action.shape == ():
            action = action.item()
        if isinstance(action, (bool, np.bool_)) or not isinstance(
                action, (int, np.integer)):
            raise ValueError("Action must be a scalar integer")
        self._transition = self.game_env.step(int(action))
        result = self._transition
        self._episode_return += result.reward
        info = dict(result.info)
        if result.terminated or result.truncated:
            info["ppo_episode"] = {
                "outcome": self._outcome(result),
                "length": self.game_env.step_count,
                "return": self._episode_return,
                "seed": self._episode_seed,
            }
        return (policy_observation(result), float(result.reward),
                result.terminated, result.truncated, info)

    def action_masks(self):
        if self._transition is None:
            raise RuntimeError(
                "Reset the environment before requesting a mask"
            )
        return policy_action_mask(self._transition)

    def _outcome(self, result):
        if result.truncated:
            return "cutoff"
        winner = result.info["outcome"].winner_player_name
        if winner is None:
            return "draw"
        return "win" if winner == self.game_env.learner.name else "loss"
