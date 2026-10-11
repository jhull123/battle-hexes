"""Masked PPO training setup and episode telemetry."""

from collections import Counter

from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import BaseCallback

from .gym_env import MaskedBattleHexesEnv


class EpisodeRecorder(BaseCallback):
    """Collect completed games and decisions from SB3's masked rollouts."""

    def __init__(self):
        super().__init__()
        self.episodes = []
        self.actions = []

    def _on_step(self):
        self.actions.append(int(self.locals["actions"][0]))
        for info in self.locals["infos"]:
            if "ppo_episode" in info:
                self.episodes.append(info["ppo_episode"])
        return True


def train(seed=0, step_limit=50, total_timesteps=256, n_steps=64,
          batch_size=32, policy_kwargs=None):
    """Train one CPU environment; return the model and observed episodes."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    for name, value in (("step_limit", step_limit),
                        ("total_timesteps", total_timesteps)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 2
           for value in (n_steps, batch_size)) or batch_size > n_steps:
        raise ValueError("require n_steps > 1 and 1 < batch_size <= n_steps")

    env = MaskedBattleHexesEnv(step_limit=step_limit, training_seed=seed)
    model = MaskablePPO(
        "MultiInputPolicy", env, seed=seed, device="cpu", verbose=0,
        n_steps=n_steps, batch_size=batch_size,
        policy_kwargs=policy_kwargs or {"net_arch": [32, 32]},
    )
    recorder = EpisodeRecorder()
    model.learn(total_timesteps=total_timesteps, callback=recorder)
    return model, recorder


def training_report(model, recorder, seed, step_limit, total_timesteps,
                    n_steps, batch_size):
    """Format outcomes and last PPO update's SB3 logger values."""
    episodes = recorder.episodes
    counts = Counter(episode["outcome"] for episode in episodes)
    metrics = model.logger.name_to_value
    mean_length = (sum(e["length"] for e in episodes) / len(episodes)
                   if episodes else None)
    mean_return = (sum(e["return"] for e in episodes) / len(episodes)
                   if episodes else None)
    lines = [
        f"seed={seed} step_limit={step_limit} "
        f"total_timesteps={total_timesteps} "
        f"n_steps={n_steps} batch_size={batch_size} device=cpu",
        f"collected_timesteps={model.num_timesteps} episodes={len(episodes)} "
        + " ".join(f"{key}={counts[key]}" for key in
                   ("win", "loss", "draw", "cutoff")),
    ]
    if episodes:
        lines.append(f"mean_length={mean_length:.3f} "
                     f"mean_return={mean_return:.3f}")
    for key in ("train/n_updates", "train/policy_gradient_loss",
                "train/value_loss", "train/entropy_loss"):
        lines.append(f"{key}={metrics.get(key, 'unavailable')}")
    return "\n".join(lines)
