#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$REPO_ROOT/.venv312/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

if ! "$PYTHON_BIN" -c 'import sys; sys.exit(sys.version_info[:2] != (3, 12))' \
    2>/dev/null; then
  echo "Python 3.12 is required; create .venv312 or activate a 3.12 environment." >&2
  exit 1
fi

export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:${PYTHONPATH:-}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

exec "$PYTHON_BIN" -m battle_agent_rl.ppo.train \
  --seed 0 --step-limit 4 --total-timesteps 32 \
  --n-steps 16 --batch-size 8 --inspect-episode 42 "$@"
