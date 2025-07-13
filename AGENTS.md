# AGENTS.md — Battle Hexes

Welcome, agents!

This repository contains two main projects:

- **`battle-hexes-web`**: the JavaScript frontend using p5.js.
- **`battle-hexes-api`**: the Python backend built with FastAPI.

See [HOW_TO_PLAY.md](HOW_TO_PLAY.md) for a primer on the core game rules.

## Helper scripts

- `api-checks.sh`: Runs unit tests and the `flake8` linter for the Python API.
  Execute this from the repository root with `./api-checks.sh`. The script runs
  in a subshell so it won't change your current working directory.

### Working with the API

- Install dependencies using both requirement files located inside the
  `battle-hexes-api` directory:
  `pip install -r battle-hexes-api/requirements.txt \
     -r battle-hexes-api/requirements-test.txt`.
- Keep code Flake8-compliant and run `./api-checks.sh` before sending a PR to
  ensure tests and linting pass.

### Working with the Web Frontend

- Install Node dependencies inside `battle-hexes-web` with `npm install`.
- Run unit tests with `npm test`.
- Agents will not be able to run integration tests (`npm run test:e2e`) because
  most environments (like the Codex sandbox) will not allow binary downloads. As such, 
  running the e2e tests is not necessary for opening a PR.
