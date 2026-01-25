#!/usr/bin/env bash

# Convenience script to run unit tests and flake8 for all Python packages.
# Assumes dependencies are installed.

set -euo pipefail

# Determine repository root directory
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Add package directories to PYTHONPATH so tests can import them
export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src:$REPO_ROOT/battle_hexes_api/src:${PYTHONPATH:-}"

# Run tests for the API package
cd "$REPO_ROOT/battle_hexes_api"
pytest

# Lint the API package
flake8 src tests
