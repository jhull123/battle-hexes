# battle-hexes

Turn-based strategy game engine.

This repository now contains several packages:

- **battle_hexes_core** – domain models like `Game`, `Board` and `Unit`.
- **battle_agent_rl** – early reinforcement learning agents. Currently includes an `RLPlayer` that performs no movement.
- **battle_hexes_api** – a FastAPI service for game lifecycle endpoints.
- **battle-hexes-web** – a p5.js web-based UI.
Source code for each project lives inside its own `src` directory (for example `battle_hexes_core/src` or `battle-hexes-web/src`) so the project name is not repeated.


From the repository root, start the development server with:

```bash
./battle_hexes_api/dev.sh
```

The launcher makes the sibling packages available without installing them.

See [HOW_TO_PLAY.md](HOW_TO_PLAY.md) for an overview of the game mechanics.

## Requirements

The targeted Python version for this project is Python 3.12.

## Setting up the API

Create a virtual environment and install the API, test, and PPO training
dependencies to run all Python checks:

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install 'torch==2.5.1+cpu' --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt -r requirements-test.txt -r requirements-ppo.txt
```

You can run unit tests and linting for all Python packages with:

```bash
./server-side-checks.sh
```

Activate `.venv312` before running this script. It checks that `python3` is
Python 3.12 and uses that interpreter for all tests and linting; CI also uses
Python 3.12.

The script runs Flake8 and Ruff. Ruff's enabled rules and settings live in
`pyproject.toml`, which is the source of truth. Run Ruff alone from the
repository root after installing `requirements-test.txt`:

```bash
python3 -m ruff check battle_hexes_core/{src,tests} battle_agent_rl/{src,tests} battle_hexes_api/{src,tests}
```

Ruff checks production source and tests in all three Python packages.
`./server-side-checks.sh` and CI run this check after Flake8.

For a quick masked-PPO training run followed by a board-level policy trace,
run `./train-and-inspect-ppo.sh` from the repository root. It uses `.venv312`
automatically; see [PPO usage](battle_agent_rl/PPO.md#run-locally) for options.

## Checking CloudFormation templates

Keep the pinned infrastructure linter in a separate Python 3.12 environment:
its SymPy requirement conflicts with the CPU Torch version used for PPO.
From the repository root:

```bash
python3.12 -m venv .venv-cfn312
.venv-cfn312/bin/python -m pip install -r requirements-infrastructure.txt
```

Run the same CloudFormation checks used by CI:

```bash
PATH="$PWD/.venv-cfn312/bin:$PATH" ./cloudformation-checks.sh
```

The script uses AWS's `cfn-lint` to check all API, database, and web
CloudFormation templates. It reports warnings and fails when it finds a
template error. The check is local and does not deploy resources or require AWS
credentials.

### Running the API with Docker

The API project includes a Dockerfile at `battle_hexes_api/Dockerfile`. From the
repository root build and run the image:

```bash
docker build -f battle_hexes_api/Dockerfile -t battle-hexes-api .
docker run -p 8000:8000 battle-hexes-api
```

The API will be available at <http://localhost:8000>.

## Setting up the Web UI

Install Node dependencies and run the frontend tests inside `battle-hexes-web`:

```bash
cd battle-hexes-web
npm install
npm test
```


## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
