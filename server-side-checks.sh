#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:$REPO_ROOT/battle_hexes_api/src:${PYTHONPATH:-}"

cd "$REPO_ROOT/battle_hexes_core"
pytest
cd "$REPO_ROOT/battle_agent_rl"
pytest
cd "$REPO_ROOT/battle_hexes_api"
pytest

cd "$REPO_ROOT"
flake8 \
  battle_hexes_core/src battle_hexes_core/tests \
  battle_agent_rl/src battle_agent_rl/tests \
  battle_hexes_api/src battle_hexes_api/tests
