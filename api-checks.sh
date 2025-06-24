#!/usr/bin/env bash

# Convenience script to run unit tests and flake8 for the Battle Hexes API.
# Assumes dependencies are installed.

set -euo pipefail

# Determine repository root directory
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$REPO_ROOT/battle-hexes-api"

# Run checks in a subshell so the caller's directory is not affected
(
  cd "$API_DIR"
  pytest
  flake8 src/ tests/
)
