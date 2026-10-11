"""Command line entry point for a bounded masked PPO training run."""

import argparse

from .training import train, training_report
from .trained_inspection import inspect_trained_episode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--step-limit", type=int, default=50)
    parser.add_argument("--total-timesteps", type=int, default=256)
    parser.add_argument("--n-steps", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--inspect-episode", type=int, metavar="SEED")
    args = parser.parse_args(argv)
    config = vars(args).copy()
    inspection_seed = config.pop("inspect_episode")
    try:
        model, recorder = train(**config)
    except ValueError as exc:
        parser.error(str(exc))
    print(training_report(model, recorder, **config))
    if inspection_seed is not None:
        inspect_trained_episode(model, inspection_seed, args.step_limit)


if __name__ == "__main__":
    main()
