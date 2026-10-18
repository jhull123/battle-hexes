#!/usr/bin/env bash
# Exercise the release image on its ARM64 target (QEMU or native ARM64).
set -euo pipefail

image="${1:?Usage: image-smoke.sh IMAGE (build with --platform linux/arm64 --load)}"
if [[ "$(docker image inspect -f '{{.Architecture}}' "$image")" != arm64 ]]; then
  echo 'Smoke test requires a linux/arm64 image' >&2
  exit 1
fi
container="$(docker run -d --rm --platform linux/arm64 --memory 512m --cpus 0.25 \
  -p 127.0.0.1::8000 "$image")"
trap 'docker logs "$container" >&2; docker rm -f "$container" >/dev/null' EXIT
port="$(docker port "$container" 8000/tcp | sed 's/.*://')"
start="$(date +%s)"
url="http://127.0.0.1:$port"
until curl -fsS "$url/health" >/dev/null 2>&1; do
  if (( $(date +%s) - start > 300 )); then
    echo 'API failed to start within 300 seconds' >&2
    exit 1
  fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$container")" != true ]]; then
    echo 'API container exited before health check' >&2
    exit 1
  fi
  sleep 1
done
echo "startup_seconds=$(( $(date +%s) - start ))"
echo "startup_memory=$(docker stats --no-stream --format '{{.MemUsage}}' "$container")"
digest="$(docker exec "$container" python -c '
import hashlib, json, os
from pathlib import Path
directory = Path(os.environ["BATTLE_HEXES_PPO_RUN_DIR"])
assert directory == Path("/app/battle_agent_rl/archive/ppo/arm64")
manifest = json.loads((directory / "manifest.json").read_text())
entry = manifest["checkpoint"]
assert entry["path"] == "checkpoint.zip"
assert hashlib.sha256((directory / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
print(entry["sha256"])
')"
echo "bundled_checkpoint_sha256=$digest"

API_URL="$url" EXPECTED_DIGEST="$digest" python3 - <<'PY'
import json
import os
from urllib.request import Request, urlopen

base = os.environ['API_URL']


def request(method, path, *, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = Request(base + path, data=data, method=method, headers={
        **({'Content-Type': 'application/json'} if data else {}),
        **(headers or {}),
    })
    with urlopen(req, timeout=300) as response:
        return json.load(response)


game = request('POST', '/games', body={
    'scenarioId': 'ppo_9x9_experimental',
    'playerTypes': ['ppo-9x9-experimental', 'human'],
}, headers={'Idempotency-Key': 'image-create-ppo'})
digest = game['ppoTurn']['checkpointDigest']
assert digest == os.environ['EXPECTED_DIGEST']
receipt = request('POST', f"/games/{game['id']}/ppo/order", headers={
    'Idempotency-Key': 'image-order-ppo',
    'Expected-Game-Version': str(game['gameVersion']),
})
assert receipt['plan']['unitId'] in ['learner-0', 'learner-1']
loaded = request('GET', f"/games/{game['id']}")
assert loaded['gameVersion'] == receipt['gameVersion']
assert loaded['ppoTurn']['checkpointDigest'] == digest
assert len(loaded['ppoTurn']['pendingUnitIds']) == 1
ordinary = request('POST', '/games', body={
    'scenarioId': 'elim_1', 'playerTypes': ['human', 'random'],
}, headers={'Idempotency-Key': 'image-create-ordinary'})
movement = request('POST', f"/games/{ordinary['id']}/movement", headers={
    'Idempotency-Key': 'image-movement-ordinary',
    'Expected-Game-Version': str(ordinary['gameVersion']),
})
assert request('GET', f"/games/{ordinary['id']}")['gameVersion'] == movement['gameVersion']
print(f"checkpoint_digest={digest} ppo_version={loaded['gameVersion']} "
      f"ordinary_version={movement['gameVersion']}")
PY
echo "steady_memory=$(docker stats --no-stream --format '{{.MemUsage}}' "$container")"
echo "peak_memory_bytes=$(docker exec "$container" cat /sys/fs/cgroup/memory.peak)"
