"""Independent, paired games using SB3-Contrib masked evaluation for PPO."""

import random

import numpy as np
from sb3_contrib.common.maskable.evaluation import evaluate_policy

from .gym_env import MaskedBattleHexesEnv


POLICIES = ("ppo", "random", "hold", "center_hold")


def _hold(env):
    unit = env.game_env.game.get_board().get_units_for_player(
        env.game_env.learner
    )[0]
    row, column = unit.get_coords()
    return row * 5 + column


def _record(
    split, checkpoint, timesteps, policy, seed, summary, length, reward
):
    if (
        summary is None
        or summary["seed"] != seed
        or summary["length"] != length
        or not np.isclose(summary["return"], reward)
        or summary["outcome"] not in ("win", "loss", "draw", "cutoff")
        or length < 1
    ):
        raise ValueError("Incomplete or inconsistent finished episode")
    return dict(
        split=split,
        checkpoint=checkpoint,
        training_timesteps=timesteps,
        policy=policy,
        game_seed=seed,
        outcome=summary["outcome"],
        length=int(length),
        **{"return": float(reward)},
    )


def _play_ppo_game(model, env):
    summaries = []

    def callback(locals_, globals_):
        for info in locals_["infos"]:
            if "ppo_episode" in info:
                summaries.append(info["ppo_episode"])

    rewards, lengths = evaluate_policy(
        model,
        env,
        n_eval_episodes=1,
        deterministic=True,
        return_episode_rewards=True,
        warn=False,
        callback=callback,
    )
    if len(summaries) != 1 or len(rewards) != 1 or len(lengths) != 1:
        raise ValueError(
            "Masked evaluation did not finish exactly one episode"
        )
    return summaries[0], lengths[0], rewards[0]


def _baseline_action(env, policy, rng, first, legal):
    if policy == "random":
        return rng.choice(legal)
    if policy == "hold":
        return _hold(env)
    if policy == "center_hold":
        return 12 if first else _hold(env)
    raise ValueError(f"Unknown policy: {policy}")


def _play_baseline_game(env, policy, seed, step_limit):
    obs, info = env.reset(seed=seed)
    rng = random.Random(seed)
    first = True
    total = 0.0
    for length in range(1, step_limit + 1):
        mask = env.action_masks()
        legal = np.flatnonzero(mask).tolist()
        action = _baseline_action(env, policy, rng, first, legal)
        if action not in legal:
            raise ValueError(
                f"Illegal {policy} action {action} for seed {seed}"
            )
        first = False
        obs, reward, terminated, truncated, info = env.step(action)
        total += reward
        if terminated or truncated:
            return info.get("ppo_episode"), length, total
    raise ValueError("Episode did not complete or cut off")


def play_game(model, policy, seed, step_limit):
    """Use a fresh environment for every policy and game seed."""
    env = MaskedBattleHexesEnv(step_limit=step_limit, training_seed=seed)
    if policy == "ppo":
        return _play_ppo_game(model, env)
    return _play_baseline_game(env, policy, seed, step_limit)


def evaluate_games(model, split, entry, seeds, step_limit):
    records = []
    for seed in seeds:
        for policy in POLICIES:
            summary, length, reward = play_game(
                model, policy, seed, step_limit
            )
            records.append(
                _record(
                    split,
                    entry["path"],
                    entry["training_timesteps"],
                    policy,
                    seed,
                    summary,
                    length,
                    reward,
                )
            )
    return records
