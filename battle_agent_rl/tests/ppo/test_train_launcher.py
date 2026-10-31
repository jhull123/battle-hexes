"""Native ARM training checks its runtime before replacing tracked files."""

import os
from pathlib import Path
import subprocess
import sys


LAUNCHER = Path(__file__).resolve().parents[2] / "train-ppo.sh"


def test_native_arm_preflight_failure_preserves_existing_artifact(tmp_path):
    script = tmp_path / "battle_agent_rl" / "train-ppo.sh"
    script.parent.mkdir()
    script.write_bytes(LAUNCHER.read_bytes())
    run_dir = script.parent / "archive" / "ppo" / "arm64"
    run_dir.mkdir(parents=True)
    manifest = run_dir / "manifest.json"
    checkpoint = run_dir / "checkpoint.zip"
    manifest.write_text("original manifest")
    checkpoint.write_bytes(b"original model")
    (tmp_path / "uname").write_text("#!/bin/sh\necho aarch64\n")
    (tmp_path / "python").write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = - ]; then\n"
        "  echo 'Native ARM64 training requires Python 3.12.' >&2\n"
        "  exit 1\n"
        "fi\n"
        "exit 99\n")
    (tmp_path / "uname").chmod(0o755)
    (tmp_path / "python").chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}

    result = subprocess.run(["bash", str(script), "arm64"], env=env,
                            capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert "Native ARM64 training requires Python 3.12" in result.stderr
    assert manifest.read_text() == "original manifest"
    assert checkpoint.read_bytes() == b"original model"


def test_native_arm_preflight_checks_shared_pins_before_replacement(tmp_path):
    script = tmp_path / "battle_agent_rl" / "train-ppo.sh"
    script.parent.mkdir()
    script.write_bytes(LAUNCHER.read_bytes())
    run_dir = script.parent / "archive" / "ppo" / "arm64"
    run_dir.mkdir(parents=True)
    manifest = run_dir / "manifest.json"
    checkpoint = run_dir / "checkpoint.zip"
    manifest.write_text("original manifest")
    checkpoint.write_bytes(b"original model")
    (tmp_path / "requirements-ppo-serving.txt").write_text(
        "-r requirements-ppo.txt\ntorch==2.5.1\n")
    (tmp_path / "requirements-ppo.txt").write_text("numpy==2.5.4\n")
    package = tmp_path / "battle_agent_rl" / "src" / "battle_agent_rl" / "ppo"
    package.mkdir(parents=True)
    (package.parent / "__init__.py").write_text("")
    (package / "__init__.py").write_text("")
    (package / "artifacts.py").write_text(
        "def versions():\n    return {'numpy': '0.0', 'torch': '2.5.1'}\n")
    (tmp_path / "uname").write_text("#!/bin/sh\necho aarch64\n")
    (tmp_path / "uname").chmod(0o755)
    (tmp_path / "python").symlink_to(sys.executable)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}

    result = subprocess.run(["bash", str(script), "arm64"], env=env,
                            capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert "pinned PPO serving libraries" in result.stderr
    assert manifest.read_text() == "original manifest"
    assert checkpoint.read_bytes() == b"original model"
