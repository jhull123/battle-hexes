#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:$REPO_ROOT/battle_hexes_api/src:${PYTHONPATH:-}"

if command -v flake8 >/dev/null 2>&1; then
  FLAKE8_CMD=(flake8)
elif python3 - <<'PY'
import importlib.util
import sys

if importlib.util.find_spec("flake8") is None:
    sys.exit(1)
PY
then
  FLAKE8_CMD=(python3 -m flake8)
else
  python3 -m pip install --quiet flake8
  FLAKE8_CMD=(python3 -m flake8)
fi

cd "$REPO_ROOT/battle_hexes_core"
pytest
cd "$REPO_ROOT/battle_agent_rl"
pytest
cd "$REPO_ROOT/battle_hexes_api"
pytest

cd "$REPO_ROOT"
NO_COLOR=1 python3 -m battle_agent_rl.ppo.rollout_inspection --seed 0 --step-limit 50 --policy random --expect-ending completed >/dev/null
NO_COLOR=1 python3 -m battle_agent_rl.ppo.rollout_inspection --seed 42 --step-limit 1 --policy hold --expect-ending cutoff >/dev/null
"${FLAKE8_CMD[@]}" \
  battle_hexes_core/src battle_hexes_core/tests \
  battle_agent_rl/src battle_agent_rl/tests \
  battle_hexes_api/src battle_hexes_api/tests
python3 -m ruff check \
  battle_hexes_core/src battle_hexes_core/tests \
  battle_agent_rl/src battle_agent_rl/tests \
  battle_hexes_api/src battle_hexes_api/tests
