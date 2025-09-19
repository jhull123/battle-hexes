# AGENTS.md — Battle Hexes

Welcome, agents!

This repository now contains multiple projects:

- **`battle_hexes_core`**: dependency-free domain classes.
- **`battle_agent_rl`**: reinforcement learning agents (work in progress).
- **`battle_hexes_api`**: the FastAPI backend using the above packages.
- **`battle-hexes-web`**: the JavaScript frontend using p5.js.
Python source files are located directly inside each project's `src` directory (e.g. `battle_hexes_core/src`).


See [HOW_TO_PLAY.md](HOW_TO_PLAY.md) for a primer on the core game rules.

## Helper scripts
Each Python project contains a `checks.sh` script that runs its unit tests and
`flake8` linter:

- `battle_hexes_core/checks.sh`
- `battle_hexes_api/checks.sh`

From the repository root you can execute `./server-side-checks.sh` to run the
tests and linter across **all** Python packages. The script adjusts
`PYTHONPATH` so the API can import the core and agent packages while tests run.

### Working with the API

- Install dependencies using both requirement files from the repository root:
  `pip install -r requirements.txt -r requirements-test.txt`.
- Keep code Flake8-compliant and run `./server-side-checks.sh` before sending a
  PR to ensure tests and linting pass.
- If flake8 is not present install it!

### Working with the Web Frontend

- Install Node dependencies inside `battle-hexes-web` with `npm install`.
- Run unit tests with `npm test`.
- Agents will not be able to run integration tests (`npm run test:e2e`) because
  most environments (like the Codex sandbox) will not allow binary downloads. As such, 
  running the e2e tests is not necessary for opening a PR.
