"""Readiness configuration and checks for runtime dependencies."""

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Callable, Mapping

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, FastAPI, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter()


@dataclass(frozen=True)
class DynamoDBConfig:
    """Validated configuration for the optional DynamoDB dependency."""

    enabled: bool
    table_name: str | None

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] = os.environ,
    ) -> "DynamoDBConfig":
        raw_enabled = environment.get("DYNAMODB_ENABLED", "false")
        normalized_enabled = raw_enabled.strip().lower()
        if normalized_enabled not in {"true", "false"}:
            raise ValueError(
                "DYNAMODB_ENABLED must be either 'true' or 'false'"
            )

        enabled = normalized_enabled == "true"
        table_name = environment.get("DDB_TABLE_NAME", "").strip() or None
        if enabled and table_name is None:
            raise ValueError(
                "DDB_TABLE_NAME is required when DynamoDB is enabled"
            )

        return cls(enabled=enabled, table_name=table_name)


class ReadinessChecker:
    """Report whether dependencies required by configuration are ready."""

    def __init__(
        self,
        config: DynamoDBConfig,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self.config = config
        self.client_factory = client_factory or (
            lambda: boto3.client("dynamodb")
        )

    def is_ready(self) -> bool:
        if not self.config.enabled:
            return True

        try:
            client = self.client_factory()
            table_response = client.describe_table(
                TableName=self.config.table_name,
            )
            ttl_response = client.describe_time_to_live(
                TableName=self.config.table_name,
            )
        except (BotoCoreError, ClientError):
            logger.warning(
                "DynamoDB readiness failure category=provider_error table=%s",
                self.config.table_name,
            )
            return False

        if not _has_required_table_contract(table_response):
            logger.warning(
                "DynamoDB readiness failure category=table_contract table=%s",
                self.config.table_name,
            )
            return False
        if not _has_required_ttl_contract(ttl_response):
            logger.warning(
                "DynamoDB readiness failure category=ttl_contract table=%s",
                self.config.table_name,
            )
            return False
        return True


def _has_required_table_contract(response: object) -> bool:
    """Return whether a DescribeTable response meets the persistence schema."""
    if not isinstance(response, Mapping):
        return False
    table = response.get("Table")
    if not isinstance(table, Mapping) or table.get("TableStatus") != "ACTIVE":
        return False

    return _has_required_key_schema(table) and _has_required_key_types(table)


def _has_required_key_schema(table: Mapping) -> bool:
    key_schema = table.get("KeySchema")
    if not isinstance(key_schema, list) or len(key_schema) != 2:
        return False
    required_keys = {("pk", "HASH"), ("sk", "RANGE")}
    actual_keys = set()
    for key in key_schema:
        if not isinstance(key, Mapping):
            return False
        attribute_name = key.get("AttributeName")
        key_type = key.get("KeyType")
        if (
            not isinstance(attribute_name, str)
            or not isinstance(key_type, str)
        ):
            return False
        actual_keys.add((attribute_name, key_type))
    if actual_keys != required_keys:
        return False
    return True


def _has_required_key_types(table: Mapping) -> bool:
    definitions = table.get("AttributeDefinitions")
    if not isinstance(definitions, list):
        return False
    attribute_types = {}
    for definition in definitions:
        if not isinstance(definition, Mapping):
            return False
        name = definition.get("AttributeName")
        if not isinstance(name, str):
            return False
        if name in attribute_types:
            return False
        attribute_types[name] = definition.get("AttributeType")
    return (
        attribute_types.get("pk") == "S"
        and attribute_types.get("sk") == "S"
    )


def _has_required_ttl_contract(response: object) -> bool:
    """Return whether a TTL description enables the expected attribute."""
    if not isinstance(response, Mapping):
        return False
    description = response.get("TimeToLiveDescription")
    return (
        isinstance(description, Mapping)
        and description.get("TimeToLiveStatus") == "ENABLED"
        and description.get("AttributeName") == "ttl"
    )


def configure_readiness(
    app: FastAPI,
    *,
    environment: Mapping[str, str] = os.environ,
    client_factory: Callable[[], object] | None = None,
) -> None:
    """Validate, log, and install the application's readiness checker."""
    config = DynamoDBConfig.from_environment(environment)
    if config.enabled:
        logger.info("DynamoDB dependency: enabled")
        logger.info("DynamoDB table: %s", config.table_name)
    else:
        logger.info("DynamoDB dependency: disabled")
        if config.table_name is not None:
            logger.warning(
                "DDB_TABLE_NAME is configured but DynamoDB is disabled"
            )
    app.state.dynamodb_config = config
    app.state.readiness_checker = ReadinessChecker(config, client_factory)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate runtime dependency configuration during startup."""
    configure_readiness(app)
    yield


@router.get("/health")
def health():
    """Health check endpoint used by load balancers."""
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request):
    """Return whether all currently required dependencies are ready."""
    if not request.app.state.readiness_checker.is_ready():
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}
