#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT/battle_hexes_core"
pytest
flake8 src/battle_hexes_core tests
