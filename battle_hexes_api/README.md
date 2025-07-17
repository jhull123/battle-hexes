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

The ``main.py`` module automatically adjusts ``PYTHONPATH`` so you can run this
command from within ``battle_hexes_api`` without installing the sibling
packages first.

## Running Tests

Use the following command to run the unit tests:

    pytest

## Running Linters

To run the `flake8` linter:

    flake8 src/ tests/

## Convenience script

You can run the checks for this package directly:

```bash
./checks.sh
```

Or from the repository root run `./server-side-checks.sh` to execute the tests
and `flake8` across all Python packages.

