# Battle Hexes API

FastAPI backend for Battle Hexes. `GET /health` provides a basic health check.

## Run locally

From the repository root, [set up Python 3.12 and install dependencies](../README.md#setting-up-the-api), then:

```sh
source .venv312/bin/activate
./battle_hexes_api/dev.sh
```

`dev.sh` makes the sibling packages importable and selects the Git-tracked PPO
model matching the host architecture. For training or replacing that model,
see [PPO.md](../battle_agent_rl/PPO.md#experimental-trained-99-game-increment-07-in-progress).

## Checks

From the repository root, run `./server-side-checks.sh` for Python tests and
linting. To check only the API, run `./battle_hexes_api/checks.sh`.

## ARM64 deployment image

From the repository root:

```sh
docker buildx build --platform linux/arm64 --provenance=false \
  -f battle_hexes_api/Dockerfile -t battle-hexes-api:ppo-arm64 --load .
./battle_hexes_api/image-smoke.sh battle-hexes-api:ppo-arm64
```

The smoke check exercises the bundled ARM64 model and ordinary game commands
over HTTP under the current 256 CPU / 512 MiB task limit. It uses in-memory
storage; it does not verify the separate durable browser-playthrough gate.
