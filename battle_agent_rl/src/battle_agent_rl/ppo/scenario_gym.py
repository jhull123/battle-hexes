"""Thin optional Gymnasium boundary over the scenario environment."""

import gymnasium as gym

from .scenario_environment import ScenarioEnvironment


class MaskedScenarioEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, task, cycle_limit=None, opponent_policy="random",
                 training_seed=0):
        super().__init__()
        self.game_env = ScenarioEnvironment(task, cycle_limit, opponent_policy)
        self.observation_space = task.observation_space()
        self.action_space = task.action_space()
        self._next_seed = training_seed
        self.episode_seeds = []
        self.last_action_legal = False

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._next_seed = seed
            self.action_space.seed(seed)
        episode_seed = self._next_seed
        self._next_seed += 1
        self.episode_seeds.append(episode_seed)
        result = self.game_env.reset(episode_seed)
        # Gym reset has no ending flags. Do not let a rollout collector predict
        # on an episode that core already completed during the opening turn.
        if result.terminated or result.truncated:
            raise RuntimeError("Reset ended before a learner decision")
        return result.observation, {
            **result.info, "episode_seed": episode_seed}

    def step(self, action):
        # The structural environment validates before any mutation. Record
        # legality after acceptance, not by unsafe array indexing.
        result = self.game_env.step(action)
        self.last_action_legal = True
        return (result.observation, float(result.reward), result.terminated,
                result.truncated, dict(result.info))

    def action_masks(self):
        return self.game_env.action_masks()
