"""Scenario-task persistence adapter behind the existing artifact interface."""

import json
import hashlib
from pathlib import Path

from sb3_contrib import MaskablePPO
import torch

from .artifacts import digest, versions, write_json
from .scenario_manifest import (
    POLICY_KWARGS, interface_record, provenance_record,
)
from .scenario_policy import ScenarioPolicy


def _algorithm_record(model):
    return {
        "learning_rate": model.learning_rate,
        "gamma": model.gamma, "gae_lambda": model.gae_lambda,
        "n_epochs": model.n_epochs, "clip_range": model.clip_range(1),
        "ent_coef": model.ent_coef, "vf_coef": model.vf_coef,
        "max_grad_norm": model.max_grad_norm,
        "normalize_advantage": model.normalize_advantage,
    }


def save_run(run_dir, model, task, *, seed, total_timesteps, n_steps,
             batch_size, episode_seeds, outcomes, changed,
             optimizer_updates=None, cycle_limit=None,
             opponent_policy="random"):
    ScenarioPolicy(model, task)  # Reject a mislabeled model before publishing.
    directory = Path(run_dir)
    directory.mkdir(parents=True, exist_ok=False)
    archive = directory / "checkpoint.zip"
    model.save(archive)
    manifest = {
        "format_version": 3, **interface_record(task),
        "provenance": provenance_record(task),
        "device": "cpu", "versions": versions(), "training_seed": seed,
        "policy": {"name": "MultiInputPolicy", "kwargs": POLICY_KWARGS},
        "training": {
            "total_timesteps": total_timesteps, "n_steps": n_steps,
            "batch_size": batch_size, "actual_timesteps": model.num_timesteps,
            "optimizer_updates": optimizer_updates,
            "ppo_epochs": model._n_updates, "episode_seeds": episode_seeds,
            "outcomes": outcomes, "parameters_changed": changed,
            "cycle_limit": cycle_limit or task.spec.turn_limit,
            "opponent_policy": opponent_policy,
            "torch_num_threads": torch.get_num_threads(),
            "algorithm": _algorithm_record(model),
        },
        "checkpoint": {"path": archive.name, "sha256": digest(archive)},
    }
    write_json(directory / "manifest.json", manifest)
    return manifest


def _validate_manifest(manifest, task):
    from .playable_artifact import _compatible_versions

    expected = interface_record(task)
    training = manifest["training"]
    entry = manifest["checkpoint"]
    provenance = manifest["provenance"]
    # Provenance is self-consistent evidence, NOT an exact-gameplay gate.
    snapshot_digest = hashlib.sha256(json.dumps(
        provenance["scenario_data"], sort_keys=True).encode()).hexdigest()
    if (manifest["format_version"] != 3 or
            any(manifest.get(k) != v for k, v in expected.items()) or
            manifest["device"] != "cpu" or
            not _compatible_versions(manifest["versions"], versions()) or
            manifest["policy"] != {"name": "MultiInputPolicy",
                                   "kwargs": POLICY_KWARGS} or
            not training["parameters_changed"] or
            training["optimizer_updates"] < 1 or
            not 1 <= training["cycle_limit"] <= task.spec.turn_limit or
            training["opponent_policy"] not in ("random", "hold") or
            entry["path"] != "checkpoint.zip" or
            not isinstance(entry["sha256"], str) or
            len(entry["sha256"]) != 64 or
            provenance["sha256"] != snapshot_digest):
        raise ValueError("Incompatible scenario PPO artifact manifest")


def read_manifest(run_dir, task):
    try:
        manifest = json.loads((Path(run_dir) / "manifest.json").read_text())
        _validate_manifest(manifest, task)
        return manifest
    except (OSError, KeyError, TypeError, AttributeError,
            json.JSONDecodeError) as error:
        raise ValueError(
            f"Invalid scenario PPO artifact: {error}") from error


def validate_artifact(run_dir, task, checkpoint_digest=None):
    manifest = read_manifest(run_dir, task)
    expected = manifest["checkpoint"]["sha256"]
    try:
        actual = digest(Path(run_dir) / "checkpoint.zip")
    except OSError as error:
        raise ValueError(f"Missing scenario checkpoint: {error}") from error
    if actual != expected or checkpoint_digest not in (None, expected):
        raise ValueError("Checkpoint digest mismatch")
    return manifest


def load_model(run_dir, task, checkpoint_digest=None):
    manifest = validate_artifact(run_dir, task, checkpoint_digest)
    model = MaskablePPO.load(Path(run_dir) / "checkpoint.zip", device="cpu")
    ScenarioPolicy(model, task)  # Check the archive's persisted binding too.
    return model, manifest
