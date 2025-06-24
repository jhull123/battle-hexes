# AGENTS.md — Battle Hexes

Welcome, agents!

This repository contains two main projects:

- **`battle-hexes-web`**: the JavaScript frontend using p5.js.
- **`battle-hexes-api`**: the Python backend built with FastAPI.

## Helper scripts

- `api-checks.sh`: Runs unit tests and the `flake8` linter for the Python API.
  Execute this from the repository root with `./api-checks.sh`.

### Working with the API

- Install dependencies using both requirement files:
  `pip install -r requirements.txt -r requirements-test.txt`.
- Keep code Flake8-compliant and run `./api-checks.sh` before sending a PR to
  ensure tests and linting pass.
