#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src"
cd "$REPO_ROOT/battle_agent_rl"
pytest -v --import-mode=importlib
flake8 .
