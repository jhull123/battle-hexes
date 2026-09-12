# battle-hexes

Turn-based strategy game engine.

This repository now contains several packages:

- **battle_hexes_core** – domain models like `Game`, `Board` and `Unit`.
- **battle_agent_rl** – early reinforcement learning agents. Currently includes an `RLPlayer` that performs no movement.
- **battle_hexes_api** – a FastAPI service for game lifecycle endpoints.
- **battle-hexes-web** – a p5.js web-based UI.
Source code for each project lives inside its own `src` directory (for example `battle_hexes_core/src` or `battle-hexes-web/src`) so the project name is not repeated.


From the ``battle_hexes_api`` directory you can run ``python -m fastapi dev src/battle_hexes_api/main.py``
to start the development server. The API module adjusts ``PYTHONPATH`` at
runtime so the sibling packages are available without installation.

See [HOW_TO_PLAY.md](HOW_TO_PLAY.md) for an overview of the game mechanics.

## Setting up the API

Create a virtual environment and install dependencies from both requirement files:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
```

You can run unit tests and linting for all Python packages with:

```bash
./server-side-checks.sh
```

## Checking CloudFormation templates

Install the pinned infrastructure linting dependencies from the repository
root:

```bash
python -m pip install -r requirements-infrastructure.txt
```

Run the same CloudFormation checks used by CI:

```bash
./cloudformation-checks.sh
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
