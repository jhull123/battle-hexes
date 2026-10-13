"""Local snapshot storage and compatibility checks for the fixed policy."""

import hashlib
import json
from pathlib import Path
import platform
from zipfile import BadZipFile

import gymnasium
import numpy
import sb3_contrib
import stable_baselines3
import torch
from sb3_contrib import MaskablePPO

from .gym_env import MaskedBattleHexesEnv


CONTRACT = "battle-hexes-5x5-1v1-occupancy-fire-remaining-v1"
SELECTION_RULE = "highest validation score; lower timesteps; checkpoint path"
BASELINES = {
    "random": "uniform sorted legal actions with random.Random(game_seed)",
    "hold": "current learner cell at every decision",
    "center_hold": "index 12 first, then current learner cell",
}


def versions():
    return dict(
        python=platform.python_version(),
        numpy=numpy.__version__,
        torch=torch.__version__,
        gymnasium=gymnasium.__version__,
        stable_baselines3=stable_baselines3.__version__,
        sb3_contrib=sb3_contrib.__version__,
    )


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _validate_policy_contract(manifest):
    if manifest["contract"] != CONTRACT or manifest["versions"] != versions():
        raise ValueError(
            "Incompatible policy-input contract or software versions"
        )
    if (
        manifest["device"] != "cpu"
        or manifest["selection_rule"] != SELECTION_RULE
        or manifest["baselines"] != BASELINES
        or manifest["interval_method"] != "completed PPO optimizer updates"
    ):
        raise ValueError("Incompatible run metadata")


def _validate_run_metadata(manifest):
    if (
        type(manifest["step_limit"]) is not int
        or manifest["step_limit"] < 1
        or manifest["step_limit"] != manifest["training"]["step_limit"]
        or not manifest["checkpoints"]
    ):
        raise ValueError("Incomplete run metadata")
    if (manifest["selected"] is not None
            and manifest["selected"] not in manifest["checkpoints"]):
        raise ValueError("Selected checkpoint is not a candidate")
    seed_sets(manifest["validation_seeds"], manifest["held_out_seeds"])
    if not isinstance(manifest["training_episode_seeds"], list):
        raise ValueError("Missing training episode seeds")
    if any(type(seed) is not int
           for seed in manifest["training_episode_seeds"]):
        raise ValueError("Invalid training episode seeds")


def _validate_checkpoints(entries):
    for entry in entries:
        if (not isinstance(entry["training_timesteps"], int)
                or entry["training_timesteps"] < 1
                or not isinstance(entry["sha256"], str)
                or len(entry["sha256"]) != 64
                or not isinstance(entry["path"], str)):
            raise ValueError("Invalid checkpoint metadata")


def read_manifest(run_dir):
    try:
        manifest = json.loads((Path(run_dir) / "manifest.json").read_text())
        _validate_policy_contract(manifest)
        _validate_run_metadata(manifest)
        _validate_checkpoints(manifest["checkpoints"])
        return manifest
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Missing or invalid run manifest: {exc}") from exc


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_checkpoint(run_dir, entry, manifest, step_limit=None):
    if step_limit is not None and step_limit != manifest["step_limit"]:
        raise ValueError("Checkpoint step limit mismatch")
    try:
        path = Path(entry["path"])
    except (KeyError, TypeError) as exc:
        raise ValueError("Missing checkpoint path") from exc
    if path.is_absolute() or ".." in path.parts or path.suffix != ".zip":
        raise ValueError("Invalid checkpoint path")
    archive = Path(run_dir) / path
    try:
        if digest(archive) != entry["sha256"]:
            raise ValueError("Checkpoint digest mismatch")
        model = MaskablePPO.load(archive, device="cpu")
    except (
        OSError,
        EOFError,
        RuntimeError,
        KeyError,
        ValueError,
        BadZipFile,
    ) as exc:
        raise ValueError(f"Invalid checkpoint {archive}: {exc}") from exc
    env = MaskedBattleHexesEnv(step_limit=manifest["step_limit"])
    if (
        model.observation_space != env.observation_space
        or model.action_space != env.action_space
    ):
        raise ValueError("Checkpoint observation/action spaces mismatch")
    return model


class SnapshotWriter:
    """Save snapshots at interval updates and the final update."""

    def __init__(self, run_dir, interval):
        if (
            isinstance(interval, bool)
            or not isinstance(interval, int)
            or interval < 1
        ):
            raise ValueError("checkpoint interval must be a positive integer")
        self.run_dir = Path(run_dir)
        self.interval = interval
        self.entries = []
        self.updates = 0

    def __call__(self, model, final=False):
        if not final:
            self.updates += 1
        if not final and self.updates % self.interval:
            return
        if (
            self.entries
            and self.entries[-1]["training_timesteps"] == model.num_timesteps
        ):
            return
        path = f"checkpoint-{model.num_timesteps:09d}.zip"
        archive = self.run_dir / path
        model.save(archive)
        self.entries.append(
            dict(
                path=path,
                training_timesteps=model.num_timesteps,
                update=self.updates,
                sha256=digest(archive),
            )
        )


def seed_sets(validation=None, held_out=None):
    validation = (
        list(range(1_000_000, 1_000_200)) if validation is None else validation
    )
    held_out = (
        list(range(2_000_000, 2_000_200)) if held_out is None else held_out
    )
    for name, seeds in (("validation", validation), ("held_out", held_out)):
        if (
            not isinstance(seeds, list)
            or not seeds
            or any(type(s) is not int for s in seeds)
            or len(seeds) != len(set(seeds))
        ):
            raise ValueError(
                f"{name} must be an ordered list of distinct integer seeds"
            )
    if set(validation) & set(held_out):
        raise ValueError("Evaluation seed sets overlap")
    return validation, held_out


def check_seed_separation(manifest):
    validation, held_out = seed_sets(
        manifest["validation_seeds"], manifest["held_out_seeds"]
    )
    if set(manifest["training_episode_seeds"]) & (
        set(validation) | set(held_out)
    ):
        raise ValueError("Evaluation seeds overlap training episodes")
