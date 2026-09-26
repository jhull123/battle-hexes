#!/usr/bin/env bash

set -euo pipefail

API_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$API_DIR/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:$API_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

cd "$API_DIR"
exec python -m fastapi dev src/battle_hexes_api/main.py "$@"
