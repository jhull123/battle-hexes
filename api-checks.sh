#!/usr/bin/env bash

# Convenience script to run unit tests and flake8 for all Python packages.
# Assumes dependencies are installed.

set -euo pipefail

# Determine repository root directory
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
# Add all package directories to PYTHONPATH so tests can import them
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_random/src:$REPO_ROOT/battle_agent_rl/src:${PYTHONPATH:-}"

# Run tests for the API
cd "$REPO_ROOT/battle_hexes_api"
pytest

# Lint all packages
cd "$REPO_ROOT"
flake8 \
  battle_hexes_api/src battle_hexes_api/tests \
  battle_hexes_core/src/battle_hexes_core \
  battle_agent_random/src/battle_agent_random \
  battle_agent_rl/src/battle_agent_rl
