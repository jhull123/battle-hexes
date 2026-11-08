"""Select and report, or reload a checkpoint for an evaluation replay."""

import argparse

from .experiment import evaluate_checkpoint, select_and_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument(
        "--checkpoint", help="replay a named manifest checkpoint"
    )
    parser.add_argument(
        "--split", choices=("validation", "held_out"), default="validation"
    )
    args = parser.parse_args(argv)
    try:
        if args.checkpoint:
            text = evaluate_checkpoint(
                args.run_dir, args.checkpoint, args.split
            )
        else:
            if args.split != "validation":
                parser.error("--split requires --checkpoint")
            text = select_and_report(args.run_dir)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(text)


if __name__ == "__main__":
    main()
