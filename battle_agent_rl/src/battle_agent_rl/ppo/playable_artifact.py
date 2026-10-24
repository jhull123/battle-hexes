"""Versioned 9x9 artifacts for frozen CPU inference."""

import hashlib
import json
import logging
import pickle
import re
from pathlib import Path
from zipfile import BadZipFile

from sb3_contrib import MaskablePPO

from .artifacts import versions, write_json
from .multi_unit_gym import multi_unit_observation_space
from .playable_scenario import (
    CONTRACT, SCENARIO_ID, SCENARIO_VERSION, SLOT_IDS, TURN_LIMIT,
    scenario_data, validate_scenario,
)


logger = logging.getLogger(__name__)


def _compatible_versions(recorded, current):
    if not isinstance(recorded, dict) or recorded.keys() != current.keys():
        return False
    if any(recorded[name] != value for name, value in current.items()
           if name != "python"):
        return False
    python_pattern = r"(\d+)\.(\d+)\.\d+"
    trained = re.fullmatch(python_pattern, recorded["python"])
    serving = re.fullmatch(python_pattern, current["python"])
    if not trained or not serving or trained.groups() != serving.groups():
        return False
    if recorded["python"] != current["python"]:
        logger.warning(
            "PPO artifact trained on Python %s; serving on Python %s "
            "(same major/minor, different patch version)",
            recorded["python"], current["python"])
    return True


def fingerprint(scenario=None):
    scenario = validate_scenario(scenario or scenario_data())
    payload = scenario.model_dump(mode="json")
    payload.pop("name", None)
    for faction in payload.get("factions", []):
        faction.pop("color", None)
        faction.pop("sounds", None)
    data = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_run(run_dir, model, *, seed, total_timesteps, n_steps, batch_size,
             episode_seeds, outcomes, changed, optimizer_updates=None):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    archive = run_dir / "checkpoint.zip"
    model.save(archive)
    entry = {"path": archive.name, "sha256": _digest(archive)}
    updates = (model._n_updates if optimizer_updates is None else
               optimizer_updates)
    manifest = {
        "format_version": 2, "contract": CONTRACT, "scenario_id": SCENARIO_ID,
        "scenario_version": SCENARIO_VERSION,
        "scenario_sha256": fingerprint(),
        "turn_limit": TURN_LIMIT, "slot_ids": list(SLOT_IDS),
        "player_types": ["ppo-9x9-experimental", "human"],
        "observation_space": repr(multi_unit_observation_space(TURN_LIMIT)),
        "action_space": "Discrete(162)", "device": "cpu",
        "versions": versions(), "training_seed": seed,
        "training": {"total_timesteps": total_timesteps, "n_steps": n_steps,
                     "batch_size": batch_size,
                     "actual_timesteps": model.num_timesteps,
                     "optimizer_updates": updates,
                     "ppo_epochs": model._n_updates,
                     "episode_seeds": episode_seeds, "outcomes": outcomes,
                     "parameters_changed": changed},
        "checkpoint": entry,
    }
    write_json(run_dir / "manifest.json", manifest)
    return manifest


def read_manifest(run_dir):
    try:
        manifest = json.loads((Path(run_dir) / "manifest.json").read_text())
        if manifest.get("scenario_sha256") != fingerprint():
            raise ValueError(
                "PPO artifact scenario fingerprint mismatch: scenario rules, "
                "units, terrain, or objectives differ from the trained "
                "scenario (name, faction colors and sounds are excluded). "
                "Regenerate the artifact manifest/checkpoint for this "
                "fingerprint."
            )
        expected = (manifest["format_version"] == 2
                    and manifest["contract"] == CONTRACT
                    and manifest["scenario_id"] == SCENARIO_ID
                    and manifest["scenario_version"] == SCENARIO_VERSION
                    and manifest["turn_limit"] == TURN_LIMIT
                    and manifest["slot_ids"] == list(SLOT_IDS)
                    and manifest["player_types"] ==
                    ["ppo-9x9-experimental", "human"]
                    and manifest["observation_space"] ==
                    repr(multi_unit_observation_space(TURN_LIMIT))
                    and manifest["action_space"] == "Discrete(162)"
                    and manifest["device"] == "cpu"
                    and _compatible_versions(manifest["versions"],
                                             versions()))
        entry = manifest["checkpoint"]
        path = Path(entry["path"])
        if (not expected or path.is_absolute() or path.parts !=
                ("checkpoint.zip",) or len(entry["sha256"]) != 64 or
                not manifest["training"]["parameters_changed"] or
                manifest["training"]["optimizer_updates"] < 1):
            raise ValueError(
                "Incompatible PPO artifact manifest: contract, scenario "
                "version, slots, player types, policy spaces, runtime "
                "versions (Python major/minor or other exact packages), "
                "or training evidence did not match"
            )
        return manifest
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Missing or invalid PPO artifact: {error}") from error


def validate_artifact(run_dir, digest=None):
    """Check the configured checkpoint's identity without loading a policy."""
    manifest = read_manifest(run_dir)
    entry = manifest["checkpoint"]
    if digest is not None and digest != entry["sha256"]:
        raise ValueError("Game-bound checkpoint identity mismatch")
    archive = Path(run_dir) / entry["path"]
    try:
        if _digest(archive) != entry["sha256"]:
            raise ValueError("Checkpoint digest mismatch")
    except OSError as error:
        raise ValueError(
            f"Missing or damaged PPO checkpoint: {error}") from error
    return manifest


def load_model(run_dir, digest=None):
    manifest = validate_artifact(run_dir, digest)
    archive = Path(run_dir) / manifest["checkpoint"]["path"]
    try:
        model = MaskablePPO.load(archive, device="cpu")
        if (model.observation_space != multi_unit_observation_space(TURN_LIMIT)
                or repr(model.action_space) != manifest["action_space"]):
            raise ValueError("Checkpoint spaces mismatch")
        return model, manifest
    except (OSError, EOFError, RuntimeError, BadZipFile, KeyError,
            AttributeError, TypeError, pickle.UnpicklingError) as error:
        raise ValueError(
            f"Missing or damaged PPO checkpoint: {error}") from error
