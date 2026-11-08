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
        # SB3 has already stepped: adapters report acceptance by the preceding
        # mask and read-only converter, before core execution.
        if env.last_action_legal:
            self.legal_actions += 1
        for info in self.locals["infos"]:
            if info.get("outcome") is not None:
                self.outcomes[info["outcome"]] += 1
        return True


def _training_environment(seed, task, cycle_limit, opponent_policy):
    if task is None:
        if cycle_limit is not None or opponent_policy != "random":
            raise ValueError("Scenario options require an explicit task")
        return (MaskedMultiUnitEnv(training_seed=seed, playable=True),
                {"net_arch": [32, 32]})
    from .scenario_gym import MaskedScenarioEnv
    from .scenario_manifest import POLICY_KWARGS
    return (MaskedScenarioEnv(task, cycle_limit, opponent_policy, seed),
            POLICY_KWARGS)


def _learn(model, recorder, total_timesteps):
    before = [param.detach().clone() for param in model.policy.parameters()]
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
    return changed, optimizer_steps


def _validate_training_config(seed, total_timesteps, n_steps, batch_size,
                              run_dir):
    if type(seed) is not int or type(total_timesteps) is not int \
            or total_timesteps < 1 or type(n_steps) is not int \
            or type(batch_size) is not int or n_steps < 2 \
            or not 1 < batch_size <= n_steps:
        raise ValueError("Require integer seed, positive timesteps and "
                         "1 < batch_size <= n_steps")
    from pathlib import Path
    if Path(run_dir).exists():
        raise ValueError("Run directory already exists")


def train(seed, total_timesteps, n_steps, batch_size, run_dir, *, task=None,
          cycle_limit=None, opponent_policy="random"):
    _validate_training_config(seed, total_timesteps, n_steps, batch_size,
                              run_dir)
    env, policy_kwargs = _training_environment(
        seed, task, cycle_limit, opponent_policy)
    model = MaskablePPO("MultiInputPolicy", env, seed=seed, device="cpu",
                        n_steps=n_steps, batch_size=batch_size, verbose=0,
                        policy_kwargs=policy_kwargs)
    if task is not None:
        from .scenario_manifest import interface_record
        model.scenario_interface = interface_record(task)
    recorder = Recorder()
    changed, optimizer_steps = _learn(model, recorder, total_timesteps)
    manifest = save_run(run_dir, model, seed=seed,
                        total_timesteps=total_timesteps, n_steps=n_steps,
                        batch_size=batch_size, episode_seeds=env.episode_seeds,
                        outcomes=dict(recorder.outcomes), changed=changed,
                        optimizer_updates=optimizer_steps, task=task,
                        cycle_limit=cycle_limit,
                        opponent_policy=opponent_policy)
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
    parser.add_argument("--scenario")
    parser.add_argument("--scenario-dir")
    parser.add_argument("--learner-seat", type=int, choices=(0, 1))
    parser.add_argument("--cycle-limit", type=int)
    parser.add_argument("--opponent-policy", choices=("random", "hold"),
                        default="random")
    args = vars(parser.parse_args())
    scenario = args.pop("scenario")
    scenario_dir = args.pop("scenario_dir")
    seat = args.pop("learner_seat")
    if bool(scenario) != (seat is not None) or (scenario_dir and not scenario):
        parser.error("--scenario and --learner-seat must be selected together")
    if scenario:
        from pathlib import Path
        from .scenario_task import ScenarioTask
        args["task"] = ScenarioTask.load(
            scenario, learner_seat=seat,
            scenario_dir=Path(scenario_dir) if scenario_dir else None)
    train(**args)


if __name__ == "__main__":
    main()
