# battle-hexes

Turn-based strategy game engine.

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

