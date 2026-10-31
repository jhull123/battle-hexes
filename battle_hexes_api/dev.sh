#!/usr/bin/env bash

set -euo pipefail

API_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$API_DIR/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:$API_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

case "$(uname -m)" in
  x86_64) PPO_ARCH=x86_64 ;;
  aarch64|arm64) PPO_ARCH=arm64 ;;
  *) printf 'Unsupported local PPO architecture: %s\n' "$(uname -m)" >&2; exit 1 ;;
esac
export BATTLE_HEXES_PPO_RUN_DIR="${BATTLE_HEXES_PPO_RUN_DIR:-$REPO_ROOT/battle_agent_rl/archive/ppo/$PPO_ARCH}"
if [[ ! -f "$BATTLE_HEXES_PPO_RUN_DIR/manifest.json" || \
      ! -f "$BATTLE_HEXES_PPO_RUN_DIR/checkpoint.zip" ]]; then
  printf 'Configured PPO artifact is incomplete: %s (expected manifest.json and checkpoint.zip)\n' \
    "$BATTLE_HEXES_PPO_RUN_DIR" >&2
fi

cd "$API_DIR"
exec python -m fastapi dev src/battle_hexes_api/main.py "$@"
