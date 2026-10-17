# Battle Hexes API

Server-side functions for Battle Hexes.

The API exposes a simple health check at `GET /health` for use with load
balancers and uptime monitoring.

## Local Set-up

Create a virtual environment.

    python3.12 -m venv .venv312

Activate the virtual environment.

    source .venv312/bin/activate

Upgrade `pip`.

    python -m pip install --upgrade pip

Install dependencies from the repository root.

    python -m pip install -r ../requirements.txt -r ../requirements-test.txt -r ../requirements-ppo.txt

## Running Locally

From this directory, start the server locally in development mode:

```bash
./dev.sh
```

The launcher makes the sibling packages available without installing them.
For local PPO development, from the repository root with the Python 3.12
environment above activated:

```sh
./battle_agent_rl/train-ppo.sh       # replaces the host architecture's model
./battle_hexes_api/dev.sh           # uses that model automatically
```

On x86, `./battle_agent_rl/train-ppo.sh arm64` instead trains the ARM64 model
locally using Docker/QEMU; ordinary x86 training and play do not require
Docker. Both models are Git-managed under `battle_agent_rl/archive/ppo/`, with
one manifest and checkpoint in each architecture directory. Training replaces
only the selected architecture's model. Commit the two files together when
updating a model. `dev.sh` uses `x86_64` or `arm64` based on the host; an
explicit `BATTLE_HEXES_PPO_RUN_DIR` still overrides it. Use the same Python
runtime to train and serve natively: the manifest rejects mismatched versions
rather than falling back to another checkpoint.

In another terminal, run
`npm run build && npm run serve` in `battle-hexes-web`, then open
`http://localhost:4173` and choose **Elimination Demo 3** and
**Trained 9×9 PPO**. The browser does not choose a checkpoint. Replacing a
model expires saved PPO games bound to its former digest; reloads show a clear
error and require a new game.

## ARM64 release image (deployment verification)

Build from the repository root with the same Dockerfile and platform as the
deployment workflow:

```sh
docker buildx build --platform linux/arm64 --provenance=false \
  -f battle_hexes_api/Dockerfile -t battle-hexes-api:ppo-arm64 --load .
./battle_hexes_api/image-smoke.sh battle-hexes-api:ppo-arm64
```

Docker is **not required for local x86 training or play**. The image smoke
test verifies the deployment artifact and resource limits. It runs the image
without an external PPO artifact override,
checks the bundled digest, makes real HTTP requests for a PPO game/order/GET
and an ordinary game/movement/GET, and prints startup time and container memory
at startup and after inference under the current 256 CPU / 512 MiB task limit.
It uses an in-memory repository; it does not replace the separate durable
backend/browser acceptance demonstration for PPO increment 07. QEMU is needed
to run ARM64 containers on x86 hosts.
The bounded verification under 256 CPU / 512 MiB took 47 seconds to start on
x86/QEMU, used 101.1 MiB at startup and 431.6 MiB after one PPO order, and
peaked at 465,440,768 bytes (about 444 MiB). This passes the current limit
for one client using in-memory storage; production DynamoDB and concurrency
have not been measured.

The image always serves the committed ARM64 model; it does not train at build,
startup or deployment. A newly committed ARM64 checkpoint expires games
bound to the previous checkpoint digest, with an explicit server/UI error.

## Running Tests

Use the following command to run the unit tests:

    pytest

## Running Linters

To run the `flake8` linter:

    flake8 src/ tests/

## Convenience script

You can run the checks for this package directly:

```bash
./checks.sh
```

Or from the repository root run `./server-side-checks.sh` to execute the tests
and `flake8` across all Python packages.
