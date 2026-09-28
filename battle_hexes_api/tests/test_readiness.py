import logging
from copy import deepcopy
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from battle_hexes_api.health.readiness import (
    DynamoDBConfig,
    ReadinessChecker,
    lifespan,
    router,
)


TABLE_NAME = "battle-hexes-dev"
VALID_TABLE_RESPONSE = {
    "Table": {
        "TableStatus": "ACTIVE",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
    }
}
VALID_TTL_RESPONSE = {
    "TimeToLiveDescription": {
        "TimeToLiveStatus": "ENABLED",
        "AttributeName": "ttl",
    }
}


def make_app():
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app


def valid_dynamodb_client():
    client = MagicMock()
    client.describe_table.return_value = deepcopy(VALID_TABLE_RESPONSE)
    client.describe_time_to_live.return_value = deepcopy(VALID_TTL_RESPONSE)
    return client


def configure_dynamodb(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENABLED", "true")
    monkeypatch.setenv("DDB_TABLE_NAME", f"  {TABLE_NAME}  ")


def ready_response(monkeypatch, dynamodb):
    configure_dynamodb(monkeypatch)
    with TestClient(make_app()) as client:
        client.app.state.readiness_checker.client_factory = lambda: dynamodb
        return client.get("/ready")


@pytest.mark.parametrize(
    ("environment", "expected"),
    [
        ({}, DynamoDBConfig(enabled=False, table_name=None)),
        (
            {"DYNAMODB_ENABLED": "  TrUe ", "DDB_TABLE_NAME": " table "},
            DynamoDBConfig(enabled=True, table_name="table"),
        ),
        (
            {"DYNAMODB_ENABLED": " FALSE ", "DDB_TABLE_NAME": " unused "},
            DynamoDBConfig(enabled=False, table_name="unused"),
        ),
    ],
)
def test_configuration_is_normalized(environment, expected):
    assert DynamoDBConfig.from_environment(environment) == expected


@pytest.mark.parametrize("enabled", ["", "yes", "1", " false-ish "])
def test_invalid_enabled_value_is_rejected(enabled):
    with pytest.raises(ValueError, match="DYNAMODB_ENABLED must be"):
        DynamoDBConfig.from_environment({"DYNAMODB_ENABLED": enabled})


@pytest.mark.parametrize("table_name", [None, "", "   "])
def test_enabled_requires_non_blank_table_name(table_name):
    environment = {"DYNAMODB_ENABLED": "true"}
    if table_name is not None:
        environment["DDB_TABLE_NAME"] = table_name

    with pytest.raises(ValueError, match="DDB_TABLE_NAME is required"):
        DynamoDBConfig.from_environment(environment)


def test_invalid_configuration_prevents_application_startup(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENABLED", "sometimes")

    with pytest.raises(ValueError, match="DYNAMODB_ENABLED must be"):
        with TestClient(make_app()):
            pass


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


def test_application_stores_one_validated_configuration(monkeypatch):
    configure_dynamodb(monkeypatch)

    with TestClient(make_app()) as client:
        config = client.app.state.dynamodb_config

        assert config == DynamoDBConfig(enabled=True, table_name=TABLE_NAME)
        assert client.app.state.readiness_checker.config is config


def test_active_compatible_table_is_ready(monkeypatch):
    dynamodb = valid_dynamodb_client()

    response = ready_response(monkeypatch, dynamodb)

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    dynamodb.describe_table.assert_called_once_with(TableName=TABLE_NAME)
    dynamodb.describe_time_to_live.assert_called_once_with(
        TableName=TABLE_NAME
    )


def test_additional_non_key_attribute_definition_is_allowed(monkeypatch):
    dynamodb = valid_dynamodb_client()
    dynamodb.describe_table.return_value["Table"][
        "AttributeDefinitions"
    ].append({"AttributeName": "other", "AttributeType": "N"})

    assert ready_response(monkeypatch, dynamodb).status_code == 200


def table_response_with(mutator):
    response = deepcopy(VALID_TABLE_RESPONSE)
    mutator(response["Table"])
    return response


def ttl_response_with(status, attribute_name="ttl"):
    return {
        "TimeToLiveDescription": {
            "TimeToLiveStatus": status,
            "AttributeName": attribute_name,
        }
    }


@pytest.mark.parametrize(
    "table_response",
    [
        None,
        {},
        {"Table": None},
        table_response_with(
            lambda table: table.update(TableStatus="UPDATING")
        ),
        table_response_with(lambda table: table.pop("KeySchema")),
        table_response_with(
            lambda table: table["KeySchema"].append(
                {"AttributeName": "extra", "KeyType": "HASH"}
            )
        ),
        table_response_with(
            lambda table: table["KeySchema"][0].update(AttributeName="id")
        ),
        table_response_with(
            lambda table: table["KeySchema"][1].update(KeyType="HASH")
        ),
        table_response_with(lambda table: table.pop("AttributeDefinitions")),
        table_response_with(
            lambda table: table["AttributeDefinitions"][0].update(
                AttributeType="N"
            )
        ),
        table_response_with(
            lambda table: table["AttributeDefinitions"].pop()
        ),
    ],
    ids=[
        "non-mapping-response",
        "missing-table",
        "malformed-table",
        "inactive",
        "missing-key-schema",
        "extra-key",
        "wrong-key-name",
        "wrong-key-type",
        "missing-definitions",
        "non-string-key",
        "missing-definition",
    ],
)
def test_incompatible_table_returns_generic_503(monkeypatch, table_response):
    dynamodb = valid_dynamodb_client()
    dynamodb.describe_table.return_value = table_response

    response = ready_response(monkeypatch, dynamodb)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}


@pytest.mark.parametrize(
    "ttl_response",
    [
        None,
        {},
        {"TimeToLiveDescription": None},
        ttl_response_with("ENABLING"),
        ttl_response_with("DISABLING"),
        ttl_response_with("DISABLED"),
        ttl_response_with("ENABLED", "expires_at"),
    ],
)
def test_incompatible_ttl_returns_generic_503(monkeypatch, ttl_response):
    dynamodb = valid_dynamodb_client()
    dynamodb.describe_time_to_live.return_value = ttl_response

    response = ready_response(monkeypatch, dynamodb)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}


@pytest.mark.parametrize(
    "operation", ["describe_table", "describe_time_to_live"]
)
@pytest.mark.parametrize(
    "error",
    [
        ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "secret",
                }
            },
            "DescribeTable",
        ),
        ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "secret"}},
            "DescribeTable",
        ),
        ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "secret"}},
            "DescribeTable",
        ),
        EndpointConnectionError(endpoint_url="https://private.example"),
    ],
)
def test_provider_error_returns_generic_503_without_logging_details(
    monkeypatch, caplog, operation, error
):
    dynamodb = valid_dynamodb_client()
    getattr(dynamodb, operation).side_effect = error

    with caplog.at_level(logging.WARNING):
        response = ready_response(monkeypatch, dynamodb)

    assert response.status_code == 503
    assert response.json() == {"detail": "Service not ready"}
    assert "secret" not in caplog.text
    assert "private.example" not in caplog.text
    assert f"category=provider_error table={TABLE_NAME}" in caplog.text


def test_health_does_not_contact_dynamodb_when_dependency_is_unavailable(
    monkeypatch,
):
    configure_dynamodb(monkeypatch)
    factory = MagicMock(
        side_effect=AssertionError("AWS must not be contacted")
    )

    with TestClient(make_app()) as client:
        client.app.state.readiness_checker.client_factory = factory
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    factory.assert_not_called()


def test_checker_accepts_an_injected_client_factory():
    dynamodb = valid_dynamodb_client()
    factory = MagicMock(return_value=dynamodb)
    checker = ReadinessChecker(
        DynamoDBConfig(enabled=True, table_name=TABLE_NAME),
        client_factory=factory,
    )

    assert checker.is_ready()
    factory.assert_called_once_with()
