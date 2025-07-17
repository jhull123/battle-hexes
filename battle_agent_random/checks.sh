#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:${PYTHONPATH:-}"
cd "$REPO_ROOT/battle_agent_random"
pytest
flake8 src tests
