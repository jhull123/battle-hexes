"""Command line entry point for a bounded masked PPO training run."""

import argparse

from .training import train, training_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--step-limit", type=int, default=50)
    parser.add_argument("--total-timesteps", type=int, default=256)
    parser.add_argument("--n-steps", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args(argv)
    try:
        model, recorder = train(**vars(args))
    except ValueError as exc:
        parser.error(str(exc))
    print(training_report(model, recorder, **vars(args)))


if __name__ == "__main__":
    main()
