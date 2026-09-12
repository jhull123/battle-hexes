import logging
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from battle_hexes_api.health.readiness import (
    DynamoDBConfig,
    lifespan,
    router,
)


def make_app():
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app


def test_dynamodb_is_disabled_by_default():
    config = DynamoDBConfig.from_environment({})

    assert config == DynamoDBConfig(enabled=False, table_name=None)


def test_ready_when_dynamodb_is_disabled_without_constructing_client(
    monkeypatch,
):
    monkeypatch.delenv("DYNAMODB_ENABLED", raising=False)
    monkeypatch.delenv("DDB_TABLE_NAME", raising=False)
    client_factory = MagicMock()

    with TestClient(make_app()) as client:
        client.app.state.readiness_checker.client_factory = client_factory
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    client_factory.assert_not_called()


def test_disabled_with_table_name_is_valid_and_warns(monkeypatch, caplog):
    monkeypatch.setenv("DYNAMODB_ENABLED", "false")
    monkeypatch.setenv("DDB_TABLE_NAME", "unused-table")

    with caplog.at_level(logging.WARNING), TestClient(make_app()) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert "configured but DynamoDB is disabled" in caplog.text


def test_active_table_is_ready(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENABLED", "true")
    monkeypatch.setenv("DDB_TABLE_NAME", "battle-hexes-dev")
    dynamodb = MagicMock()
    dynamodb.describe_table.return_value = {
        "Table": {"TableStatus": "ACTIVE"}
    }

    with TestClient(make_app()) as client:
        client.app.state.readiness_checker.client_factory = lambda: dynamodb
        response = client.get("/ready")

    assert response.status_code == 200
    dynamodb.describe_table.assert_called_once_with(
        TableName="battle-hexes-dev"
    )


@pytest.mark.parametrize("table_name", [None, "", "   "])
def test_enabled_requires_non_blank_table_name(monkeypatch, table_name):
    monkeypatch.setenv("DYNAMODB_ENABLED", "true")
    if table_name is None:
        monkeypatch.delenv("DDB_TABLE_NAME", raising=False)
    else:
        monkeypatch.setenv("DDB_TABLE_NAME", table_name)

    with pytest.raises(ValueError, match="DDB_TABLE_NAME is required"):
        with TestClient(make_app()):
            pass


def test_invalid_enabled_value_fails_startup(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENABLED", "sometimes")

    with pytest.raises(ValueError, match="DYNAMODB_ENABLED must be"):
        with TestClient(make_app()):
            pass


def ready_response_for_dynamodb(monkeypatch, dynamodb):
    monkeypatch.setenv("DYNAMODB_ENABLED", "true")
    monkeypatch.setenv("DDB_TABLE_NAME", "battle-hexes-dev")
    with TestClient(make_app()) as client:
        client.app.state.readiness_checker.client_factory = lambda: dynamodb
        return client.get("/ready")


def test_table_not_found_returns_503(monkeypatch):
    dynamodb = MagicMock()
    dynamodb.describe_table.side_effect = ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "no"}},
        "DescribeTable",
    )

    response = ready_response_for_dynamodb(monkeypatch, dynamodb)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}


def test_boto_error_returns_503(monkeypatch):
    dynamodb = MagicMock()
    dynamodb.describe_table.side_effect = EndpointConnectionError(
        endpoint_url="https://dynamodb.example"
    )

    response = ready_response_for_dynamodb(monkeypatch, dynamodb)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}


def test_non_active_table_returns_503(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENABLED", "true")
    monkeypatch.setenv("DDB_TABLE_NAME", "battle-hexes-dev")
    dynamodb = MagicMock()
    dynamodb.describe_table.return_value = {
        "Table": {"TableStatus": "CREATING"}
    }

    with TestClient(make_app()) as client:
        client.app.state.readiness_checker.client_factory = lambda: dynamodb
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}
