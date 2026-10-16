#!/usr/bin/env bash

set -euo pipefail

API_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$API_DIR/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:$API_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

# Use the bounded local PPO smoke artifact when it exists. An explicit
# environment setting always wins, so deployments can bind games to their
# configured run without changing this development launcher.
DEFAULT_PPO_RUN_DIR="/tmp/opencode/ppo-07-smoke-v2"
if [[ -z "${BATTLE_HEXES_PPO_RUN_DIR:-}" ]]; then
  if [[ -f "$DEFAULT_PPO_RUN_DIR/manifest.json" && \
        -f "$DEFAULT_PPO_RUN_DIR/checkpoint.zip" ]]; then
    export BATTLE_HEXES_PPO_RUN_DIR="$DEFAULT_PPO_RUN_DIR"
    printf 'Using experimental PPO artifact: %s\n' \
      "$BATTLE_HEXES_PPO_RUN_DIR" >&2
  else
    printf '%s\n' \
      'Experimental PPO unavailable: BATTLE_HEXES_PPO_RUN_DIR is unset and the local smoke artifact was not found.' \
      'Set BATTLE_HEXES_PPO_RUN_DIR to a run directory containing manifest.json and checkpoint.zip to enable it.' \
      >&2
  fi
elif [[ ! -f "$BATTLE_HEXES_PPO_RUN_DIR/manifest.json" || \
        ! -f "$BATTLE_HEXES_PPO_RUN_DIR/checkpoint.zip" ]]; then
  printf 'Configured PPO artifact is incomplete: %s (expected manifest.json and checkpoint.zip)\n' \
    "$BATTLE_HEXES_PPO_RUN_DIR" >&2
fi

cd "$API_DIR"
exec python -m fastapi dev src/battle_hexes_api/main.py "$@"
