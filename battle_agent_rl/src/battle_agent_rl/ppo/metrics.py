"""Outcome accounting, paired comparisons and predeclared bootstrap."""

from collections import Counter
import random
from statistics import mean, median

from .evaluation import POLICIES


def game_score(record):
    return {"win": 1.0, "draw": 0.5, "loss": 0.0, "cutoff": 0.0}[
        record["outcome"]
    ]


def paired(records):
    by_policy = {policy: {} for policy in POLICIES}
    for record in records:
        policy = record["policy"]
        seed = record["game_seed"]
        if policy not in by_policy or seed in by_policy[policy]:
            raise ValueError("Duplicate or unknown policy/seed record")
        by_policy[policy][seed] = record
    seeds = set(by_policy["ppo"])
    if not seeds or any(set(group) != seeds for group in by_policy.values()):
        raise ValueError("Incomplete paired evaluation records")
    return by_policy


def summarize(records):
    groups = paired(records)
    result = {}
    for policy, games in groups.items():
        values = list(games.values())
        counts = Counter(r["outcome"] for r in values)
        count = len(values)
        result[policy] = dict(
            games=count,
            counts={k: counts[k] for k in ("win", "loss", "draw", "cutoff")},
            rates={
                k: counts[k] / count for k in ("win", "loss", "draw", "cutoff")
            },
            mean_length=mean(r["length"] for r in values),
            median_length=median(r["length"] for r in values),
            mean_return=mean(r["return"] for r in values),
            score=mean(game_score(r) for r in values),
        )
    result["ppo"]["paired_differences"] = {
        policy: mean(
            game_score(groups["ppo"][s]) - game_score(groups[policy][s])
            for s in sorted(groups["ppo"])
        )
        for policy in POLICIES
        if policy != "ppo"
    }
    return result


def bootstrap(records):
    groups = paired(records)
    seeds = sorted(groups["ppo"])
    generator = random.Random(0)
    differences = {p: [] for p in POLICIES if p != "ppo"}
    for _ in range(10_000):
        sample = generator.choices(seeds, k=len(seeds))
        for policy in differences:
            differences[policy].append(
                mean(
                    game_score(groups["ppo"][s])
                    - game_score(groups[policy][s])
                    for s in sample
                )
            )
    result = {}
    for policy, values in differences.items():
        values.sort()
        result[policy] = dict(
            difference=mean(
                game_score(groups["ppo"][s]) - game_score(groups[policy][s])
                for s in seeds
            ),
            interval=[values[249], values[9749]],
        )
    if all(v["interval"][0] > 0 for v in result.values()):
        conclusion = "improvement supported"
    elif any(v["interval"][1] < 0 for v in result.values()):
        conclusion = "worse"
    else:
        conclusion = "inconclusive"
    return result, conclusion


def score_interval(records):
    """Percentile interval for PPO's unpaired score in one seed set."""
    games = paired(records)["ppo"]
    scores = [game_score(games[s]) for s in sorted(games)]
    generator = random.Random(0)
    samples = sorted(
        mean(generator.choices(scores, k=len(scores))) for _ in range(10_000)
    )
    return [samples[249], samples[9749]]


def select(results):
    """Select using validation PPO scores only; stable tie-breaks."""
    if not results:
        raise ValueError("No validation candidates")
    return min(
        results,
        key=lambda pair: (
            -summarize(pair[1])["ppo"]["score"],
            pair[0]["training_timesteps"],
            pair[0]["path"],
        ),
    )[0]


def table(entry, summary):
    """Format a compact outcome table and separate paired-score comparisons."""
    lines = [
        f"Checkpoint: {entry['path']}  |  Collected steps: "
        f"{entry['training_timesteps']}",
        "",
        "Outcomes and episode metrics",
        "Policy               Games  W/L/D/C       "
        "Win/Loss/Draw/Cutoff %   Decisions μ/med  Return    Score",
        "-------------------- -----  ------------  "
        "----------------------   --------------  --------   -----",
    ]
    for policy in POLICIES:
        row = summary[policy]
        counts = row["counts"]
        rates = row["rates"]
        name = {"center_hold": "center-then-hold"}.get(policy, policy)
        outcome_counts = "/".join(
            str(counts[k]) for k in ("win", "loss", "draw", "cutoff")
        )
        outcome_rates = "/".join(
            f"{100 * rates[k]:.1f}" for k in
            ("win", "loss", "draw", "cutoff")
        )
        lines.append(
            f"{name:<20} {row['games']:>5}  {outcome_counts:>12}  "
            f"{outcome_rates:>22}  "
            f"{row['mean_length']:>6.2f}/{row['median_length']:<6.2f}  "
            f"{row['mean_return']:>8.3f}     {row['score']:>5.3f}"
        )
    differences = summary["ppo"].get("paired_differences", {})
    if differences:
        lines.extend(("", "Paired score difference (PPO − baseline)",
                      "Baseline          Difference"))
        for policy in ("random", "hold", "center_hold"):
            name = {"center_hold": "center-then-hold"}.get(policy, policy)
            lines.append(f"{name:<17} {differences[policy]:>+9.3f}")
    lines.append(
        "Counts/rates are W/L/D/cutoff; score = "
        "(wins + 0.5 × draws) / games."
    )
    return "\n".join(lines)
