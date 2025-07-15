#!/usr/bin/env bash

# Convenience script to run unit tests and flake8 for all Python packages.
# Assumes dependencies are installed.

set -euo pipefail

# Determine repository root directory
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
# Add all package directories to PYTHONPATH so tests can import them
export PYTHONPATH="$REPO_ROOT/battle-hexes-core:$REPO_ROOT/battle-agent-random:$REPO_ROOT/battle-agent-rl:${PYTHONPATH:-}"

# Run tests for the API
cd "$REPO_ROOT/battle-hexes-api"
pytest

# Lint all packages
cd "$REPO_ROOT"
flake8 \
  battle-hexes-api/src battle-hexes-api/tests \
  battle-hexes-core/battle_hexes_core \
  battle-agent-random/battle_agent_random \
  battle-agent-rl/battle_agent_rl
