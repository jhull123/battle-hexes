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
  PR to ensure tests and linting pass. If `flake8` is missing from the
  environment, install it before running the checks (e.g. `pip install flake8`).

### Working with the Web Frontend

- Install Node dependencies inside `battle-hexes-web` with `npm install`.
- Run unit tests with `npm test`.
- Agents will not be able to run integration tests (`npm run test:e2e`) because
  most environments (like the Codex sandbox) will not allow binary downloads. As such, 
  running the e2e tests is not necessary for opening a PR.

## Change quality guidance

- Prefer small, focused methods; avoid introducing long methods when a few well-named helpers would make the logic easier to read.
- Keep cyclomatic complexity reasonable by extracting branching logic into helper functions or dedicated classes when behavior grows beyond a straightforward flow.
- Prefer testing observable behavior and public contracts over incidental implementation details.
- Do not add tests that assert exact log message text, private helper calls, or other brittle internals unless the log/output is itself part of documented behavior or an explicit operational requirement.

## Naming and Casing

This repository follows a canonical naming/casing policy. Follow these rules when
adding or modifying code, samples, and tests:

- **Python internals:** Use snake_case for variables, functions, methods, and
  model/attribute names (including Pydantic model attributes).
- **Scenario JSON:** Keep scenario files in snake_case; do not convert existing
  scenario JSON to camelCase as part of normal changes.
- **HTTP API JSON:** Use camelCase for request and response JSON (the
  client-facing contract consumed by the frontend).
- **Frontend / JavaScript:** Use camelCase for properties, method names, and
  frontend model fields.

## End-to-end scenario change guidance

- Read `documentation/end-to-end-change-instructions.md` when a task adds,
  removes, renames, or changes the behavior of data that starts in scenario JSON
  and must flow through the core loader/domain model, API serialization, and the
  web frontend.
- You usually do not need to read it for isolated bug fixes, refactors, tests,
  documentation-only work, UI changes that do not touch scenario-backed data, or
  backend/frontend changes that do not alter scenario file properties. Prefer
  skipping it in those cases to keep context and token usage focused on the task.

## Specification docs

- Place all implementation/design specs in the repository `specs/` directory (use a feature-specific subdirectory when helpful).
- Do not leave new spec files in project package directories unless explicitly requested.
- Do not perform code changes when creating a specification unless explicitly requested.
- Include an "Open Questions" section at the end of the spec to clarify any ambiguities that need to be resolved for implementation. If there are no such ambiguities then simply list state "No questions." in this section. Do not create questions just to fill out this section. The questions should be useful, essential, and limited. 
