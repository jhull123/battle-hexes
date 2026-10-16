"""Gymnasium adapter for the incompatible 9x9 multi-unit contract."""

import gymnasium as gym
import numpy as np

from .multi_unit_environment import MultiUnitEnvironment
from .playable_environment import PlayableEnvironment
from .multi_unit_state import ACTIONS, CONTRACT


def encode_observation(observation):
    binary = ("positions", "present", "alive", "defensive_fire_ready",
              "fire_eligible_last_turn", "forced_retreat", "fire_spent",
              "pending")
    return {key: np.array(value, dtype=np.int8 if key in binary or
                          key == "movement_remaining" else np.int32)
            for key, value in observation.items()}


def predict_joint_action(model, observation, mask):
    """Reject 1v1 and other incompatible policies before prediction."""
    if not isinstance(model.observation_space, gym.spaces.Dict) or \
            "remaining_cycles" not in model.observation_space.spaces or \
            model.observation_space != multi_unit_observation_space(
                int(model.observation_space["remaining_cycles"].high[0])) \
            or model.action_space != gym.spaces.Discrete(ACTIONS):
        raise ValueError(f"Incompatible policy for {CONTRACT}")
    encoded = encode_observation(observation)
    if not model.observation_space.contains(encoded) or len(mask) != ACTIONS:
        raise ValueError(f"Incompatible inputs for {CONTRACT}")
    action, _ = model.predict(
        encoded, action_masks=np.asarray(mask, dtype=np.bool_),
        deterministic=True)
    return int(action)


def multi_unit_observation_space(cycle_limit):
    return gym.spaces.Dict({
        "positions": gym.spaces.MultiBinary((4, 81)),
        "present": gym.spaces.MultiBinary(4),
        "alive": gym.spaces.MultiBinary(4),
        "movement_remaining": gym.spaces.Box(0, 2, (4,), dtype=np.int8),
        "defensive_fire_ready": gym.spaces.MultiBinary(4),
        "fire_eligible_last_turn": gym.spaces.MultiBinary(4),
        "forced_retreat": gym.spaces.MultiBinary(4),
        "fire_spent": gym.spaces.MultiBinary(4),
        "pending": gym.spaces.MultiBinary(2),
        "remaining_cycles": gym.spaces.Box(
            0, cycle_limit, (1,), dtype=np.int32),
    })


class MaskedMultiUnitEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, cycle_limit=50, training_seed=0, learner_count=2,
                 opponent_count=2, playable=False):
        super().__init__()
        self.game_env = (PlayableEnvironment(cycle_limit) if playable else
                         MultiUnitEnvironment(cycle_limit, learner_count,
                                              opponent_count))
        self.observation_space = multi_unit_observation_space(
            50 if playable else cycle_limit)
        self.action_space = gym.spaces.Discrete(ACTIONS)
        self._next_seed = training_seed
        self._transition = None
        self.episode_seeds = []

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._next_seed = seed
            self.action_space.seed(seed)
        episode_seed = self._next_seed
        self._next_seed += 1
        self.episode_seeds.append(episode_seed)
        self._transition = self.game_env.reset(episode_seed)
        return encode_observation(self._transition.observation), {
            **self._transition.info, "episode_seed": episode_seed}

    def step(self, action):
        if isinstance(action, np.ndarray) and action.shape == ():
            action = action.item()
        self.last_action_legal = bool(
            self._transition.legal_action_mask[action])
        self._transition = self.game_env.step(action)
        result = self._transition
        return (encode_observation(result.observation), float(result.reward),
                result.terminated, result.truncated, dict(result.info))

    def action_masks(self):
        if self._transition is None:
            raise RuntimeError("Reset before requesting a mask")
        return np.array(self._transition.legal_action_mask, dtype=np.bool_)
