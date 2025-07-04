# Battle Hexes API

Server-side functions for Battle Hexes.

## Local Set-up

Create a virtual environment.

    python -m venv .venv

Activate the virtual environment.

    source .venv/bin/activate

Upgrade `pip`.

    python -m pip install --upgrade pip

Install dependencies.

    pip install -r requirements.txt -r requirements-test.txt

## Running Locally

To start the server locally in development mode:

    fastapi dev src/main.py

## Running Tests

Use the following command to run the unit tests:

    pytest

## Running Linters

To run the `flake8` linter:

    flake8 src/ tests/

## Convenience script

From the repository root you can run `./api-checks.sh` to execute both the tests
and `flake8` together. This is useful before committing code.

