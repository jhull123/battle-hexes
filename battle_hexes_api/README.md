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

    python -m pip install -r ../requirements.txt -r ../requirements-test.txt

## Running Locally

From this directory, start the server locally in development mode:

```bash
./dev.sh
```

The launcher makes the sibling packages available without installing them.
If `/tmp/opencode/ppo-07-smoke-v2` contains `manifest.json` and
`checkpoint.zip`, the launcher automatically configures it for the experimental
9×9 PPO player. To use another trained run, set
`BATTLE_HEXES_PPO_RUN_DIR=/path/to/run` before starting `./dev.sh`. The
configured directory is inherited by the API process; it is not enough to set
the variable in a separate shell after the server has started.

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
