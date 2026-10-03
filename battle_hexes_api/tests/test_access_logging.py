import logging

import pytest

from battle_hexes_api.access_logging import HealthCheckAccessLogFilter


@pytest.mark.parametrize("path", ["/health", "/ready"])
def test_successful_health_check_access_logs_are_filtered(path):
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "server.py",
        1,
        '%s - "%s %s HTTP/%s" %s',
        ("127.0.0.1", "GET", path, "1.1", 200),
        None,
    )

    assert not HealthCheckAccessLogFilter().filter(record)


@pytest.mark.parametrize(
    ("path", "status"),
    [("/ready", 503), ("/health", 500), ("/game", 200)],
)
def test_failure_and_non_health_access_logs_are_retained(path, status):
    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "server.py",
        1,
        '%s - "%s %s HTTP/%s" %s',
        ("127.0.0.1", "GET", path, "1.1", status),
        None,
    )

    assert HealthCheckAccessLogFilter().filter(record)
