#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

if ! command -v cfn-lint >/dev/null 2>&1; then
  echo "cfn-lint is required; install requirements-infrastructure.txt" >&2
  exit 1
fi

cfn-lint --non-zero-exit-code error \
  battle_hexes_api/dev-database.yml \
  battle_hexes_api/ecs-backend.yml \
  battle-hexes-web/cloudformation-template.yml
