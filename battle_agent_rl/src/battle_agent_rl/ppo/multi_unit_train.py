"""Bounded playable masked-PPO smoke trainer."""

import argparse
from collections import Counter

import torch
from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import BaseCallback

from .multi_unit_gym import MaskedMultiUnitEnv
from .playable_artifact import save_run


class Recorder(BaseCallback):
    def __init__(self):
        super().__init__()
        self.outcomes = Counter()
        self.legal_actions = 0

    def _on_step(self):
        env = self.training_env.envs[0].unwrapped
        # SB3 has already stepped: verify actions against the preceding mask
        # using the mask cached by the environment immediately before stepping.
        if env.last_action_legal:
            self.legal_actions += 1
        for info in self.locals["infos"]:
            if info.get("outcome") is not None:
                self.outcomes[info["outcome"]] += 1
        return True


def train(seed, total_timesteps, n_steps, batch_size, run_dir):
    if type(seed) is not int or type(total_timesteps) is not int \
            or total_timesteps < 1 or type(n_steps) is not int \
            or type(batch_size) is not int or n_steps < 2 \
            or not 1 < batch_size <= n_steps:
        raise ValueError("Require integer seed, positive timesteps and "
                         "1 < batch_size <= n_steps")
    from pathlib import Path
    if Path(run_dir).exists():
        raise ValueError("Run directory already exists")
    env = MaskedMultiUnitEnv(training_seed=seed, playable=True)
    model = MaskablePPO("MultiInputPolicy", env, seed=seed, device="cpu",
                        n_steps=n_steps, batch_size=batch_size, verbose=0,
                        policy_kwargs={"net_arch": [32, 32]})
    before = [param.detach().clone() for param in model.policy.parameters()]
    recorder = Recorder()
    optimizer_steps = 0

    def count_step(_optimizer, _args, _kwargs):
        nonlocal optimizer_steps
        optimizer_steps += 1

    hook = model.policy.optimizer.register_step_post_hook(count_step)
    try:
        model.learn(total_timesteps=total_timesteps, callback=recorder)
    finally:
        hook.remove()
    changed = any(not torch.equal(old, new) for old, new in zip(
        before, model.policy.parameters()))
    if not changed or optimizer_steps < 1 or recorder.legal_actions != \
            model.num_timesteps:
        raise RuntimeError(
            "PPO training did not produce legal updated weights")
    manifest = save_run(run_dir, model, seed=seed,
                        total_timesteps=total_timesteps, n_steps=n_steps,
                        batch_size=batch_size, episode_seeds=env.episode_seeds,
                        outcomes=dict(recorder.outcomes), changed=changed,
                        optimizer_updates=optimizer_steps)
    print(f"manifest={run_dir}/manifest.json steps={model.num_timesteps} "
          f"optimizer_updates={optimizer_steps} epochs={model._n_updates} "
          f"legal={recorder.legal_actions} "
          f"outcomes={dict(recorder.outcomes)}")
    return model, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--total-timesteps", type=int, default=64)
    parser.add_argument("--n-steps", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--run-dir", required=True)
    train(**vars(parser.parse_args()))


if __name__ == "__main__":
    main()
