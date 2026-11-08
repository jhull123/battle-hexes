"""Existing trainer/artifact entry points, actual learning and legal reload."""

from copy import deepcopy
import json
import shutil

import pytest
import torch

from battle_agent_rl.ppo.multi_unit_train import train
from battle_agent_rl.ppo.playable_artifact import (
    load_model, read_manifest, validate_artifact,
)
from battle_agent_rl.ppo.scenario_environment import ScenarioEnvironment
from battle_agent_rl.ppo.scenario_policy import ScenarioPolicy
from battle_agent_rl.ppo.scenario_task import ScenarioTask


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    task = ScenarioTask.load("d_day_crossroads", learner_seat=1)
    directory = tmp_path_factory.mktemp("scenario") / "smoke"
    model, manifest = train(23, 16, 16, 8, directory, task=task,
                            cycle_limit=2, opponent_policy="hold")
    return directory, model, manifest, task


def replay(model, task, seed):
    policy = ScenarioPolicy(model, task)
    env = ScenarioEnvironment(task, opponent_policy="hold")
    transition = env.reset(seed)
    trace = [transition.info]
    while not env.done:
        action = policy.predict(transition.observation,
                                transition.legal_action_mask)
        assert transition.legal_action_mask[action]
        transition = env.step(action)
        trace.append(transition.info)
    assert transition.terminated and not transition.truncated
    return trace


def test_real_masked_learning_reload_and_frozen_legal_replay(trained):
    directory, model, manifest, task = trained
    training = manifest["training"]
    assert training["parameters_changed"]
    assert training["actual_timesteps"] == 16
    assert training["optimizer_updates"] == 20
    assert training["ppo_epochs"] == 10
    assert training["episode_seeds"] == [23, 24, 25]
    assert sum(training["outcomes"].values()) == 2
    assert manifest["learner_seat"] == 1
    assert manifest["core_player_order"] == ["Player 1", "Player 2"]
    assert manifest["provenance"]["scenario_data"]["id"] == task.scenario_id
    assert manifest["reward"]["perspective"] == "learner"
    reloaded, loaded = load_model(directory, task=task)
    assert loaded == manifest
    weights = [p.detach().clone() for p in reloaded.policy.parameters()]
    assert replay(model, task, 1000) == replay(reloaded, task, 1000)
    assert all(torch.equal(a, b) for a, b in zip(
        weights, reloaded.policy.parameters()))


@pytest.mark.parametrize("field,value", [
    ("contract", "battle-hexes-crossroads-airborne-draft-v1"),
    ("contract", "battle-hexes-crossroads-wehrmacht-"
     "unit-destination-live-turnlimit8-v1"),
    ("learner_seat", 0), ("slot_ids", ["wrong"]),
    ("observation_space", {}), ("action_space", {"n": 162}),
    ("scenario_id", "ppo_5x5"), ("scenario_version", "superseded"),
    ("core_player_order", ["Player 2", "Player 1"]),
    ("versions", {}), ("checkpoint", {"path": "../checkpoint.zip"}),
])
def test_manifest_mismatches_reject_before_loading(
        trained, tmp_path, monkeypatch, field, value):
    directory, model, manifest, task = trained
    from sb3_contrib import MaskablePPO
    monkeypatch.setattr(MaskablePPO, "load", lambda *a, **k:
                        pytest.fail("Incompatible archive was deserialized"))
    changed = {**manifest, field: value}
    (tmp_path / "manifest.json").write_text(json.dumps(changed))
    with pytest.raises(ValueError):
        load_model(tmp_path, task=task)


def test_legacy_artifacts_cannot_be_relabeled_or_used_without_task(
        trained, tmp_path):
    directory, _, manifest, task = trained
    with pytest.raises(ValueError):
        load_model(directory)  # 07 does not adopt 08 artifacts.
    for legacy in ({"format_version": 1, "contract": "5x5"},
                   {"format_version": 2, "contract": "9x9"}):
        (tmp_path / "manifest.json").write_text(json.dumps(legacy))
        with pytest.raises(ValueError):
            load_model(tmp_path, task=task)


def test_archive_binding_spaces_and_digest_are_independently_checked(
        trained, tmp_path):
    directory, model, manifest, task = trained
    from battle_agent_rl.ppo.artifacts import digest
    changed_model = deepcopy(model)
    changed_model.scenario_interface["learner_seat"] = 0
    changed_model.save(tmp_path / "checkpoint.zip")
    changed = deepcopy(manifest)
    changed["checkpoint"]["sha256"] = digest(tmp_path / "checkpoint.zip")
    (tmp_path / "manifest.json").write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="Incompatible"):
        load_model(tmp_path, task=task)
    shutil.copy(directory / "checkpoint.zip", tmp_path / "checkpoint.zip")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    assert validate_artifact(tmp_path, task=task) == manifest
    with pytest.raises(ValueError, match="digest"):
        validate_artifact(tmp_path, "0" * 64, task=task)
    (tmp_path / "checkpoint.zip").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="digest"):
        load_model(tmp_path, task=task)


def test_compatible_gameplay_variation_is_not_an_exact_scenario_gate(trained):
    directory, _, manifest, task = trained
    payload = task.scenario.model_dump(mode="json")
    # Changes gameplay but not declared representation/identity/bounds.
    payload["stacking_limit"] = 3
    changed = ScenarioTask(task.scenario.model_validate(payload), 1)
    assert read_manifest(directory, task=changed) == manifest


@pytest.mark.parametrize("seat", [0, 1])
def test_unregistered_task_uses_same_trainer_and_artifact_interface(
        small_scenario, tmp_path, seat):
    scenario = small_scenario.model_copy(update={"id": "editor-policy"})
    (tmp_path / "editor-policy.json").write_text(scenario.model_dump_json())
    task = ScenarioTask.load("editor-policy", learner_seat=seat,
                             scenario_dir=tmp_path)
    directory = tmp_path / "trained"
    _, manifest = train(7, 2, 2, 2, directory, task=task,
                        cycle_limit=1, opponent_policy="hold")
    model, loaded = load_model(directory, task=task)
    assert loaded == manifest and manifest["learner_seat"] == seat
    env = ScenarioEnvironment(task, opponent_policy="hold")
    result = env.reset(0)
    action = ScenarioPolicy(model, task).predict(
        result.observation, result.legal_action_mask)
    assert result.legal_action_mask[action]
