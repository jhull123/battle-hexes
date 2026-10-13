"""Predeclared experiment protocol and durable evaluation reports."""

from pathlib import Path

from .artifacts import (
    BASELINES,
    CONTRACT,
    SELECTION_RULE,
    SnapshotWriter,
    check_seed_separation,
    load_checkpoint,
    read_manifest,
    seed_sets,
    versions,
    write_json,
)
from .evaluation import evaluate_games
from .metrics import bootstrap, score_interval, select, summarize, table
from .training import train


def train_run(run_dir, interval, validation=None, held_out=None, **config):
    run_dir = Path(run_dir)
    validation, held_out = seed_sets(validation, held_out)
    writer = SnapshotWriter(run_dir, interval)
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = dict(
        contract=CONTRACT,
        versions=versions(),
        device="cpu",
        interval_method="completed PPO optimizer updates",
        checkpoint_interval=interval,
        selection_rule=SELECTION_RULE,
        baselines=BASELINES,
        training=config,
        step_limit=config["step_limit"],
        validation_seeds=validation,
        held_out_seeds=held_out,
        training_episode_seeds=[],
        checkpoints=[],
        selected=None,
    )
    # Persist the protocol before model comparisons or any evaluation.
    write_json(run_dir / "manifest.json", manifest)
    model, recorder = train(**config, snapshot_hook=writer)
    manifest["training_episode_seeds"] = recorder.episode_seeds
    manifest["checkpoints"] = writer.entries
    manifest["collected_timesteps"] = model.num_timesteps
    check_seed_separation(manifest)
    write_json(run_dir / "manifest.json", manifest)
    return model, recorder


def _evaluate(run_dir, manifest, entry, split):
    model = load_checkpoint(run_dir, entry, manifest)
    return evaluate_games(
        model, split, entry, manifest[f"{split}_seeds"], manifest["step_limit"]
    )


def _save_report(run_dir, name, records, text, report):
    write_json(Path(run_dir) / f"{name}-episodes.json", records)
    write_json(Path(run_dir) / f"{name}-report.json", report)
    (Path(run_dir) / f"{name}-table.txt").write_text(text + "\n")
    return text


def _select_on_validation(run_dir, manifest):
    entries = sorted(
        manifest["checkpoints"],
        key=lambda e: (e["training_timesteps"], e["path"]),
    )
    validation = [
        (e, _evaluate(run_dir, manifest, e, "validation")) for e in entries
    ]
    selected = select(validation)
    validation_text = "\n\n".join(
        table(e, summarize(records)) for e, records in validation
    )
    validation_text += (
        f"\nSelection rule: {SELECTION_RULE}\n"
        f"Selected: {selected['path']} sha256={selected['sha256']}"
    )
    _save_report(
        run_dir,
        "validation",
        [record for _, records in validation for record in records],
        validation_text,
        dict(
            selection_rule=SELECTION_RULE,
            selected=selected,
            progression=[
                dict(checkpoint=e, metrics=summarize(r)) for e, r in validation
            ],
        ),
    )
    selected_records = next(
        records for entry, records in validation if entry == selected
    )
    return selected, selected_records


def _report_held_out(run_dir, manifest, selected, selected_validation):
    held = _evaluate(run_dir, manifest, selected, "held_out")
    comparisons, conclusion = bootstrap(held)
    validation_intervals, _ = bootstrap(selected_validation)
    text = table(selected, summarize(held))
    validation_score_interval = score_interval(selected_validation)
    held_score_interval = score_interval(held)
    text += (
        f"\nSelected sha256={selected['sha256']}\n"
        f"Held-out paired 95% intervals (10,000 seed resamples):\n"
    )
    for policy, result in comparisons.items():
        text += f"{policy}: {result['difference']:+.3f} {result['interval']}\n"
    text += (
        f"Conclusion: {conclusion}. Cutoff is core in_progress, neither a "
        "loss nor a draw (score 0).\n"
        "Validation vs held-out PPO scores: "
        f"{summarize(selected_validation)['ppo']['score']:.3f} "
        f"{validation_score_interval} vs "
        f"{summarize(held)['ppo']['score']:.3f} "
        f"{held_score_interval}; independent seed sets "
        "may differ. Review large differences for selection overfitting.\n"
    )
    result = _save_report(
        run_dir,
        "held-out",
        held,
        text,
        dict(
            selected=selected,
            metrics=summarize(held),
            paired_intervals=comparisons,
            validation_paired_intervals=validation_intervals,
            validation_score_interval=validation_score_interval,
            held_out_score_interval=held_score_interval,
            conclusion=conclusion,
        ),
    )
    return result


def select_and_report(run_dir):
    manifest = read_manifest(run_dir)
    check_seed_separation(manifest)
    if manifest["selected"] is not None:
        raise ValueError("Selection already reported for this run")
    selected, selected_validation = _select_on_validation(run_dir, manifest)
    result = _report_held_out(
        run_dir, manifest, selected, selected_validation
    )
    manifest["selected"] = selected
    write_json(Path(run_dir) / "manifest.json", manifest)
    return result


def evaluate_checkpoint(run_dir, checkpoint, split="validation"):
    manifest = read_manifest(run_dir)
    check_seed_separation(manifest)
    if split not in ("validation", "held_out"):
        raise ValueError("Invalid split")
    entry = next(
        (e for e in manifest["checkpoints"] if e["path"] == checkpoint), None
    )
    if entry is None:
        raise ValueError("Checkpoint not in run manifest")
    if split == "held_out" and entry != manifest["selected"]:
        raise ValueError(
            "Held-out evaluation requires frozen selected checkpoint"
        )
    records = _evaluate(run_dir, manifest, entry, split)
    text = table(entry, summarize(records))
    return _save_report(
        run_dir,
        f"replay-{split}-{Path(checkpoint).stem}",
        records,
        text,
        dict(checkpoint=entry, metrics=summarize(records)),
    )
