#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:$REPO_ROOT/battle_hexes_api/src:${PYTHONPATH:-}"

python3 - <<'PY'
import sys

if sys.version_info[:2] != (3, 12):
    print(
        f"Server-side checks require Python 3.12; got {sys.version.split()[0]} "
        f"from {sys.executable}. Activate .venv312 first: "
        "source .venv312/bin/activate",
        file=sys.stderr,
    )
    sys.exit(1)
PY

if ! python3 -c 'import flake8' >/dev/null 2>&1; then
  python3 -m pip install --quiet flake8
fi

cd "$REPO_ROOT/battle_hexes_core"
python3 -m pytest
cd "$REPO_ROOT/battle_agent_rl"
python3 -m pytest
cd "$REPO_ROOT/battle_hexes_api"
python3 -m pytest

cd "$REPO_ROOT"
NO_COLOR=1 python3 -m battle_agent_rl.ppo.rollout_inspection --seed 0 --step-limit 50 --policy random --expect-ending completed >/dev/null
NO_COLOR=1 python3 -m battle_agent_rl.ppo.rollout_inspection --seed 42 --step-limit 1 --policy hold --expect-ending cutoff >/dev/null
python3 -m flake8 \
  battle_hexes_core/src battle_hexes_core/tests \
  battle_agent_rl/src battle_agent_rl/tests \
  battle_hexes_api/src battle_hexes_api/tests
python3 -m ruff check \
  battle_hexes_core/src battle_hexes_core/tests \
  battle_agent_rl/src battle_agent_rl/tests \
  battle_hexes_api/src battle_hexes_api/tests
