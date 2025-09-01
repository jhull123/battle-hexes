#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Repo root is ${REPO_ROOT}"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:${PYTHONPATH:-}"
echo "Python path is ${PYTHONPATH}"
python "$REPO_ROOT/battle_agent_rl/src/battle_agent_rl/qmultiunittrainer.py" "$@"
