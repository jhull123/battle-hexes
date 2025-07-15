# battle-hexes

Turn-based strategy game engine.

This repository now contains several Python packages:

- **battle_hexes_core** – domain models like `Game`, `Board` and `Unit`.
- **battle_agent_random** – a simple `RandomPlayer` implementation.
- **battle_agent_rl** – a placeholder for reinforcement learning agents.
- **battle_hexes_api** – a FastAPI service for game lifecycle endpoints.

From the ``battle_hexes_api`` directory you can run ``fastapi dev src/main.py``
to start the development server. The API module adjusts ``PYTHONPATH`` at
runtime so the sibling packages are available without installation.

See [HOW_TO_PLAY.md](HOW_TO_PLAY.md) for an overview of the game mechanics.

## Setting up the API

Create a virtual environment and install dependencies from both requirement files:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r battle-hexes-api/requirements.txt -r battle-hexes-api/requirements-test.txt
```

You can run unit tests and linting together with:

```bash
./api-checks.sh
```

