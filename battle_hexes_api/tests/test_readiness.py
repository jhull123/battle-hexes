"""Startup contract and process-local readiness behavior."""

import logging
from copy import deepcopy
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from battle_hexes_api.health.config import DynamoDBConfig
from battle_hexes_api.health.readiness import router
from battle_hexes_api.health.startup import (
    _has_required_keys,
    configure_dependencies,
    lifespan,
)

TABLE_NAME = "battle-hexes-dev"
TABLE_RESPONSE = {
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
TTL_RESPONSE = {
    "TimeToLiveDescription": {
        "TimeToLiveStatus": "ENABLED",
        "AttributeName": "ttl",
    }
}


def make_app():
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app


def dynamodb_client():
    client = MagicMock()
    client.describe_table.return_value = deepcopy(TABLE_RESPONSE)
    client.describe_time_to_live.return_value = deepcopy(TTL_RESPONSE)
    return client


def enabled_app(monkeypatch, dynamodb):
    monkeypatch.setenv("DYNAMODB_ENABLED", "true")
    monkeypatch.setenv("DDB_TABLE_NAME", f"  {TABLE_NAME}  ")
    monkeypatch.setattr(
        "battle_hexes_api.health.startup.boto3.client",
        lambda service, **kwargs: dynamodb,
    )
    return make_app()


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


def test_in_memory_mode_does_not_contact_aws(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENABLED", "false")
    monkeypatch.delenv("DDB_TABLE_NAME", raising=False)
    factory = MagicMock(side_effect=AssertionError("AWS contact"))
    app = make_app()
    configure_dependencies(app, environment={}, client_factory=factory)
    assert app.state.dynamodb_config == DynamoDBConfig(False, None)
    factory.assert_not_called()


def test_disabled_with_table_name_warns(monkeypatch, caplog):
    monkeypatch.setenv("DYNAMODB_ENABLED", "false")
    monkeypatch.setenv("DDB_TABLE_NAME", "unused-table")
    with caplog.at_level(logging.WARNING), TestClient(make_app()) as client:
        assert client.get("/ready").status_code == 200
    assert "configured but DynamoDB is disabled" in caplog.text


def test_startup_validates_contract_once(monkeypatch):
    dynamodb = dynamodb_client()
    with TestClient(enabled_app(monkeypatch, dynamodb)) as client:
        config = client.app.state.dynamodb_config
        assert config == DynamoDBConfig(enabled=True, table_name=TABLE_NAME)
        assert client.get("/ready").status_code == 200
        assert client.get("/ready").status_code == 200
    dynamodb.describe_table.assert_called_once_with(TableName=TABLE_NAME)
    dynamodb.describe_time_to_live.assert_called_once_with(
        TableName=TABLE_NAME
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda table: table.pop("KeySchema"),
        lambda table: table["KeySchema"][0].update(AttributeName="id"),
        lambda table: table["KeySchema"][1].update(KeyType="HASH"),
        lambda table: table["AttributeDefinitions"][0].update(
            AttributeType="N"
        ),
    ],
)
def test_wrong_key_contract_fails_startup(monkeypatch, change):
    dynamodb = dynamodb_client()
    change(dynamodb.describe_table.return_value["Table"])
    with pytest.raises(RuntimeError, match="incompatible key schema"):
        with TestClient(enabled_app(monkeypatch, dynamodb)):
            pass


def test_additional_non_key_definition_is_allowed():
    table = deepcopy(TABLE_RESPONSE["Table"])
    table["AttributeDefinitions"].append(
        {"AttributeName": "other", "AttributeType": "N"}
    )
    assert _has_required_keys(table)


def test_ttl_mismatch_warns_without_blocking_traffic(monkeypatch, caplog):
    dynamodb = dynamodb_client()
    dynamodb.describe_time_to_live.return_value = {
        "TimeToLiveDescription": {
            "TimeToLiveStatus": "DISABLED",
            "AttributeName": "ttl",
        }
    }
    with caplog.at_level(logging.WARNING):
        with TestClient(enabled_app(monkeypatch, dynamodb)) as client:
            assert client.get("/ready").status_code == 200
    assert "category=ttl_contract" in caplog.text


def test_ttl_check_failure_warns_without_blocking_traffic(
    monkeypatch, caplog
):
    dynamodb = dynamodb_client()
    dynamodb.describe_time_to_live.side_effect = EndpointConnectionError(
        endpoint_url="https://private.example"
    )
    with caplog.at_level(logging.WARNING):
        with TestClient(enabled_app(monkeypatch, dynamodb)) as client:
            assert client.get("/ready").status_code == 200
    assert "category=ttl_unverified" in caplog.text
    assert "private.example" not in caplog.text


@pytest.mark.parametrize("status", ["ACTIVE", "UPDATING"])
def test_usable_table_passes_startup(monkeypatch, status):
    dynamodb = dynamodb_client()
    dynamodb.describe_table.return_value["Table"]["TableStatus"] = status
    with TestClient(enabled_app(monkeypatch, dynamodb)) as client:
        assert client.get("/ready").status_code == 200


def test_unavailable_table_fails_startup(monkeypatch):
    dynamodb = dynamodb_client()
    dynamodb.describe_table.return_value["Table"]["TableStatus"] = "CREATING"
    with pytest.raises(RuntimeError, match="unavailable at startup"):
        with TestClient(enabled_app(monkeypatch, dynamodb)):
            pass


def test_provider_error_fails_startup_without_exposing_details(monkeypatch):
    dynamodb = dynamodb_client()
    dynamodb.describe_table.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "secret"}},
        "DescribeTable",
    )
    with pytest.raises(RuntimeError, match="could not be validated") \
            as error:
        with TestClient(enabled_app(monkeypatch, dynamodb)):
            pass
    assert "secret" not in str(error.value)


def test_ready_does_not_contact_aws_after_startup(monkeypatch):
    dynamodb = dynamodb_client()
    with TestClient(enabled_app(monkeypatch, dynamodb)) as client:
        dynamodb.describe_table.reset_mock()
        dynamodb.describe_time_to_live.reset_mock()
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    dynamodb.describe_table.assert_not_called()
    dynamodb.describe_time_to_live.assert_not_called()


def test_health_does_not_contact_dynamodb(monkeypatch):
    dynamodb = dynamodb_client()
    with TestClient(enabled_app(monkeypatch, dynamodb)) as client:
        dynamodb.describe_table.reset_mock()
        dynamodb.describe_time_to_live.reset_mock()
        assert client.get("/health").status_code == 200
    dynamodb.describe_table.assert_not_called()
    dynamodb.describe_time_to_live.assert_not_called()
