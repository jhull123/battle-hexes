"""Lossless task-interface metadata, distinct from gameplay provenance."""

from dataclasses import asdict
import hashlib
import json

import numpy as np
from gymnasium import spaces


POLICY_KWARGS = {"net_arch": {"pi": [64, 64], "vf": [64, 64]}}
REWARD = {"win": 1, "loss": -1, "draw": 0, "cutoff": 0,
          "perspective": "learner", "timing": "once at core completion"}


def space_record(space):
    """Record exact dtypes/bounds, not abbreviated Box reprs."""
    if isinstance(space, spaces.Dict):
        return {key: space_record(value)
                for key, value in space.spaces.items()}
    record = {"type": type(space).__name__, "shape": list(space.shape),
              "dtype": str(space.dtype)}
    if isinstance(space, spaces.Box):
        for name in ("low", "high"):
            values = getattr(space, name)
            record[name] = (values.flat[0].item() if values.size and
                            np.all(values == values.flat[0]) else
                            values.tolist())
    elif isinstance(space, spaces.Discrete):
        record.update(n=int(space.n), start=int(space.start))
    elif not isinstance(space, spaces.MultiBinary):
        raise ValueError("Unsupported policy space")
    return record


def interface_record(task):
    binding = task.create_game(None)  # Raw core configuration, no transitions.
    players = binding.game.players
    return {
        "contract": task.contract, "scenario_id": task.scenario_id,
        "scenario_version": task.scenario_version,
        "decision_spec": json.loads(json.dumps(asdict(task.spec))),
        "learner_seat": task.learner_seat,
        "core_player_order": [p.name for p in players],
        "scoring_seat": (players.index(binding.scoring_player)
                         if binding.scoring_player is not None else None),
        "slot_ids": list(task.spec.slot_ids),
        "turn_limit": task.spec.turn_limit,
        "observation_space": space_record(task.observation_space()),
        "action_space": space_record(task.action_space()),
        "reward": dict(REWARD),
    }


def provenance_record(task):
    snapshot = task.scenario.model_dump(mode="json")
    digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode())
    return {"scenario_data": snapshot, "sha256": digest.hexdigest()}
