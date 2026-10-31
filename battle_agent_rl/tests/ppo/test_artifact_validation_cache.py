"""Validation reuse must retain integrity and compatibility guarantees."""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from battle_agent_rl.ppo import playable_artifact as artifacts


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    source = Path(__file__).parents[2] / "archive/ppo/x86_64/manifest.json"
    manifest = json.loads(source.read_text())
    archive = tmp_path / "checkpoint.zip"
    archive.write_bytes(b"checkpoint contents")
    manifest["checkpoint"]["sha256"] = hashlib.sha256(
        archive.read_bytes()).hexdigest()
    manifest["versions"] = artifacts.versions()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    hashes = []
    original = artifacts._digest

    def digest(path):
        hashes.append(path)
        return original(path)

    monkeypatch.setattr(artifacts, "_digest", digest)
    return tmp_path, manifest, hashes


def test_concurrent_validation_reuses_hash_and_checks_every_game(artifact):
    run_dir, manifest, hashes = artifact
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(artifacts.validate_artifact, [run_dir] * 8))
    assert len(hashes) == 1
    results[0]["checkpoint"]["sha256"] = "0" * 64
    assert artifacts.validate_artifact(run_dir) == manifest
    with pytest.raises(ValueError, match="Game-bound"):
        artifacts.validate_artifact(run_dir, "0" * 64)
    assert artifacts.validate_artifact(
        run_dir, manifest["checkpoint"]["sha256"]) == manifest
    assert len(hashes) == 1


@pytest.mark.parametrize("filename", ["manifest.json", "checkpoint.zip"])
def test_atomic_replacement_revalidates_even_with_same_bytes(
        artifact, filename):
    run_dir, _, hashes = artifact
    artifacts.validate_artifact(run_dir)
    path = run_dir / filename
    replacement = run_dir / "replacement"
    replacement.write_bytes(path.read_bytes())
    replacement.replace(path)
    artifacts.validate_artifact(run_dir)
    assert len(hashes) == 2


def test_same_size_write_with_restored_mtime_is_rejected(artifact):
    run_dir, _, hashes = artifact
    artifacts.validate_artifact(run_dir)
    path = run_dir / "checkpoint.zip"
    before = path.stat()
    path.write_bytes(b"X" * before.st_size)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(ValueError, match="digest mismatch"):
        artifacts.validate_artifact(run_dir)
    with pytest.raises(ValueError, match="digest mismatch"):
        artifacts.validate_artifact(run_dir)
    assert len(hashes) == 3  # Failed validations are never cached.


@pytest.mark.parametrize("filename", ["manifest.json", "checkpoint.zip"])
def test_missing_files_are_rejected_after_success(artifact, filename):
    run_dir, _, _ = artifact
    artifacts.validate_artifact(run_dir)
    (run_dir / filename).unlink()
    with pytest.raises(ValueError, match="Missing"):
        artifacts.validate_artifact(run_dir)


@pytest.mark.parametrize("content", ["{", None])
def test_changed_manifest_is_revalidated(artifact, content):
    run_dir, manifest, _ = artifact
    artifacts.validate_artifact(run_dir)
    manifest["contract"] = "incompatible"
    (run_dir / "manifest.json").write_text(
        content if content is not None else json.dumps(manifest))
    with pytest.raises(ValueError):
        artifacts.validate_artifact(run_dir)


def test_change_during_hash_is_not_cached(artifact, monkeypatch):
    run_dir, _, _ = artifact
    original = artifacts._digest

    def changing_digest(path):
        result = original(path)
        with path.open("ab") as archive:
            archive.write(b"changed")
        return result

    monkeypatch.setattr(artifacts, "_digest", changing_digest)
    with pytest.raises(ValueError, match="changed during validation"):
        artifacts.validate_artifact(run_dir)
    monkeypatch.setattr(artifacts, "_digest", original)
    with pytest.raises(ValueError, match="digest mismatch"):
        artifacts.validate_artifact(run_dir)
