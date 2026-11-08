"""Command line entry point for a bounded masked PPO training run."""

import argparse
import json
from pathlib import Path

from .experiment import train_run
from .training import train, training_report
from .trained_inspection import inspect_trained_episode


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--step-limit", type=int, default=50)
    parser.add_argument("--total-timesteps", type=int, default=256)
    parser.add_argument("--n-steps", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--inspect-episode", type=int, metavar="SEED")
    parser.add_argument(
        "--run-dir", help="new local directory for checkpoint artifacts"
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        help="completed optimizer updates between snapshots",
    )
    parser.add_argument(
        "--seed-lists",
        help="JSON with validation and held_out ordered seed lists",
    )
    return parser


def _run_training(args):
    config = vars(args).copy()
    config.pop("inspect_episode")
    run_dir = config.pop("run_dir")
    interval = config.pop("checkpoint_interval")
    seed_lists = config.pop("seed_lists")
    if run_dir is None:
        if interval is not None or seed_lists is not None:
            raise ValueError(
                "--checkpoint-interval/--seed-lists require --run-dir"
            )
        model, recorder = train(**config)
    else:
        if interval is None:
            raise ValueError("--run-dir requires --checkpoint-interval")
        seeds = (
            json.loads(Path(seed_lists).read_text()) if seed_lists else {}
        )
        if set(seeds) - {"validation", "held_out"}:
            raise ValueError("Unknown seed-list role")
        model, recorder = train_run(
            run_dir,
            interval,
            validation=seeds.get("validation"),
            held_out=seeds.get("held_out"),
            **config,
        )
    return model, recorder, config


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        model, recorder, config = _run_training(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(training_report(model, recorder, **config))
    if args.inspect_episode is not None:
        inspect_trained_episode(model, args.inspect_episode, args.step_limit)


if __name__ == "__main__":
    main()
