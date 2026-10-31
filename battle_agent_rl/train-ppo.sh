#!/usr/bin/env bash
# Replace exactly one Git-tracked architecture's local PPO model on request.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="${1:-$(uname -m)}"
if (( $# > 1 )); then
  echo 'Usage: ./battle_agent_rl/train-ppo.sh [x86_64|arm64]' >&2
  exit 1
fi
case "$ARCH" in
  x86_64|amd64) ARCH=x86_64 ;;
  arm64|aarch64) ARCH=arm64 ;;
  *) echo "Unsupported PPO architecture: $ARCH" >&2; exit 1 ;;
esac

MODEL_ROOT="$REPO_ROOT/battle_agent_rl/archive/ppo"
RUN_DIR="$MODEL_ROOT/$ARCH"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

if [[ "$ARCH" == arm64 && "$(uname -m)" == x86_64 ]]; then
  # Build the training stage before touching the existing checkpoint.
  docker buildx build --platform linux/arm64 --provenance=false \
    --target ppo-training -f "$REPO_ROOT/battle_hexes_api/Dockerfile" \
    -t battle-hexes-ppo-training:arm64 --load "$REPO_ROOT"
  train=(docker run --rm --platform linux/arm64 \
    -e OMP_NUM_THREADS -e MKL_NUM_THREADS -e HOME=/tmp \
    -e MPLCONFIGDIR=/tmp/matplotlib \
    -u "$(id -u):$(id -g)" -v "$MODEL_ROOT:/models" \
    --entrypoint python battle-hexes-ppo-training:arm64 \
    -m battle_agent_rl.ppo.multi_unit_train)
  model_path=/models/arm64
else
  if [[ "$ARCH" == x86_64 && "$(uname -m)" != x86_64 ]]; then
    echo 'x86_64 training requires an x86_64 host.' >&2
    exit 1
  fi
  export PYTHONPATH="$REPO_ROOT/battle_hexes_core/src:$REPO_ROOT/battle_agent_rl/src${PYTHONPATH:+:$PYTHONPATH}"
  if [[ "$ARCH" == arm64 ]]; then
    if ! python - "$REPO_ROOT/requirements-ppo-serving.txt" <<'PY'
import sys
from pathlib import Path

if sys.version_info[:2] != (3, 12):
    sys.exit('Native ARM64 training requires Python 3.12.')

from battle_agent_rl.ppo.artifacts import versions

def pinned_versions(path):
    expected = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.partition('#')[0].strip()
        if line.startswith('-r '):
            expected.update(pinned_versions(path.parent / line[3:].strip()))
        elif '==' in line:
            name, version = line.split('==', 1)
            expected[name.strip().replace('-', '_')] = version.strip()
    return expected


expected = pinned_versions(Path(sys.argv[1]))
actual = versions()
if any(actual.get(name) != version for name, version in expected.items()):
    sys.exit('Native ARM64 training requires the pinned PPO serving libraries.')
PY
    then
      exit 1
    fi
  fi
  python -c 'import battle_agent_rl.ppo.multi_unit_train'  # check dependencies first
  train=(python -m battle_agent_rl.ppo.multi_unit_train)
  model_path="$RUN_DIR"
fi

mkdir -p "$MODEL_ROOT"
if [[ -L "$RUN_DIR" || ( -e "$RUN_DIR" && ! -d "$RUN_DIR" ) ]]; then
  echo "Refusing to replace a non-directory PPO model: $RUN_DIR" >&2
  exit 1
fi
if [[ -d "$RUN_DIR" ]]; then
  # Do not discard unfamiliar files; evaluation output is not part of the model.
  unexpected="$(find "$RUN_DIR" -mindepth 1 -maxdepth 1 \
    ! -name manifest.json ! -name checkpoint.zip ! -name evaluation.json \
    -print -quit)"
  if [[ -n "$unexpected" ]]; then
    echo "Refusing to delete unexpected file: $unexpected" >&2
    exit 1
  fi
  rm -f -- "$RUN_DIR/manifest.json" "$RUN_DIR/checkpoint.zip" \
    "$RUN_DIR/evaluation.json"
  rmdir -- "$RUN_DIR"
fi

"${train[@]}" --seed 0 --total-timesteps 16 --n-steps 16 --batch-size 8 \
  --run-dir "$model_path"
echo "Trained $ARCH PPO model in $RUN_DIR (commit manifest.json and checkpoint.zip)."
