"""Local launcher selects the tracked model for the host architecture."""

import os
from pathlib import Path
import subprocess

import pytest


LAUNCHER = Path(__file__).resolve().parents[1] / "dev.sh"
REPO_ROOT = LAUNCHER.parent.parent


@pytest.mark.parametrize("machine,architecture", [
    ("x86_64", "x86_64"), ("aarch64", "arm64"),
])
@pytest.mark.parametrize("override", [None, "/my/ppo/model"])
def test_dev_uses_host_checkpoint_unless_overridden(
        tmp_path, machine, architecture, override):
    (tmp_path / "uname").write_text(f"#!/bin/sh\necho {machine}\n")
    (tmp_path / "python").write_text(
        '#!/bin/sh\nprintf "%s\\n" "$BATTLE_HEXES_PPO_RUN_DIR"\n')
    (tmp_path / "uname").chmod(0o755)
    (tmp_path / "python").chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    env.pop("BATTLE_HEXES_PPO_RUN_DIR", None)
    if override is not None:
        env["BATTLE_HEXES_PPO_RUN_DIR"] = override

    result = subprocess.run(
        ["bash", str(LAUNCHER)], env=env, capture_output=True,
        text=True, check=True,
    )
    expected = override or str(
        REPO_ROOT / "battle_agent_rl/archive/ppo" / architecture)
    assert result.stdout.strip() == expected
