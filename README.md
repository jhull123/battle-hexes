# battle-hexes

Turn-based strategy game engine.

This repository now contains several packages:

- **battle_hexes_core** – domain models like `Game`, `Board` and `Unit`.
- **battle_agent_random** – a simple `RandomPlayer` implementation.
- **battle_agent_rl** – a placeholder for reinforcement learning agents.
- **battle_hexes_api** – a FastAPI service for game lifecycle endpoints.
- **battle-hexes-web** – a p5.js web-based UI.
Source code for each project lives inside its own `src` directory (for example `battle_hexes_core/src` or `battle-hexes-web/src`) so the project name is not repeated.


From the ``battle_hexes_api`` directory you can run ``fastapi dev src/main.py``
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

## Setting up the Web UI

Install Node dependencies and run the frontend tests inside `battle-hexes-web`:

```bash
cd battle-hexes-web
npm install
npm test
```

