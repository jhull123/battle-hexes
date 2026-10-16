"""Bounded deterministic checkpoint replay with core-completion accounting."""

import argparse
from collections import Counter

from .artifacts import write_json
from .multi_unit_gym import predict_joint_action
from .playable_artifact import load_model
from .playable_environment import PlayableEnvironment


def evaluate(run_dir, seeds=range(1000, 1020), cycle_limit=50):
    model, manifest = load_model(run_dir)
    seeds = list(seeds)
    if (not seeds or len(seeds) != len(set(seeds)) or
            any(type(seed) is not int for seed in seeds) or
            set(seeds) & set(manifest["training"]["episode_seeds"])):
        raise ValueError("Evaluation seeds must be unique and disjoint")
    results = []
    for seed in seeds:
        env = PlayableEnvironment(cycle_limit)
        state = env.reset(seed)
        while not state.terminated and not state.truncated:
            action = predict_joint_action(
                model, state.observation, state.legal_action_mask)
            state = env.step(action)
        results.append({"gameSeed": seed, "outcome": state.info["outcome"],
                        "learnerDecisions": state.info["decision_count"],
                        "coreStatus": state.info["core_status"]})
    counts = Counter(row["outcome"] for row in results)
    report = {"checkpointDigest": manifest["checkpoint"]["sha256"],
              "cycleLimit": cycle_limit, "seeds": seeds, "episodes": results,
              "counts": {key: counts[key] for key in
                         ("win", "loss", "draw", "cutoff")}}
    from pathlib import Path
    write_json(Path(run_dir) / "evaluation.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--seeds", default="1000:1020")
    parser.add_argument("--cycle-limit", type=int, default=50)
    args = parser.parse_args()
    start, stop = map(int, args.seeds.split(":"))
    if start >= stop:
        parser.error("seeds must be a nonempty start:stop range")
    report = evaluate(args.run_dir, range(start, stop), args.cycle_limit)
    print(f"evaluation={args.run_dir}/evaluation.json {report['counts']}")


if __name__ == "__main__":
    main()
