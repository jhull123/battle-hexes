#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:${PYTHONPATH:-}"
exec python3 -m battle_agent_rl.ppo.rollout_inspection "$@"
