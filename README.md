# battle-hexes

Turn-based strategy game engine.

This repository now contains several Python packages:

- **battle-hexes-core** – domain models like `Game`, `Board` and `Unit`.
- **battle-agent-random** – a simple `RandomPlayer` implementation.
- **battle-agent-rl** – a placeholder for reinforcement learning agents.
- **battle-hexes-api** – a FastAPI service for game lifecycle endpoints.

From the ``battle-hexes-api`` directory you can run ``fastapi dev src/main.py``
to start the development server. The API module adjusts ``PYTHONPATH`` at
runtime so the sibling packages are available without installation.

See [HOW_TO_PLAY.md](HOW_TO_PLAY.md) for an overview of the game mechanics.

