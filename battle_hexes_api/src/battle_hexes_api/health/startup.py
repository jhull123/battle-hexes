"""Validate DynamoDB configuration and deployment invariants at startup."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Callable, Mapping

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI

from .config import DynamoDBConfig
from .dependency_probe import DynamoDBReadinessProbe, PROBE_INTERVAL_SECONDS

logger = logging.getLogger(__name__)


def configure_dependencies(
    app: FastAPI,
    *,
    environment: Mapping[str, str] = os.environ,
    client_factory: Callable[[], object] | None = None,
) -> None:
    """Install one validated config and check static deployment invariants."""
    config = DynamoDBConfig.from_environment(environment)
    factory = client_factory or (
        lambda: boto3.client(
            "dynamodb",
            config=Config(
                connect_timeout=2,
                read_timeout=2,
                retries={"mode": "standard", "total_max_attempts": 1},
            ),
        )
    )
    if config.enabled:
        logger.info(
            "DynamoDB dependency: enabled; table=%s", config.table_name
        )
        try:
            client = factory()
        except (BotoCoreError, ClientError):
            raise RuntimeError(
                "DynamoDB table contract could not be validated"
            ) from None
        _validate_table_contract(client, config.table_name)
        probe = DynamoDBReadinessProbe(client, config.table_name)
        probe.probe_once()
        app.state.dynamodb_readiness_probe = probe
    else:
        logger.info("DynamoDB dependency: disabled")
        if config.table_name is not None:
            logger.warning(
                "DDB_TABLE_NAME is configured but DynamoDB is disabled"
            )
    app.state.dynamodb_config = config


def _validate_table_contract(client, table_name):
    try:
        table_response = client.describe_table(TableName=table_name)
    except (BotoCoreError, ClientError):
        raise RuntimeError(
            "DynamoDB table contract could not be validated"
        ) from None

    table = table_response.get("Table") if isinstance(table_response, dict) \
        else None
    if not isinstance(table, dict) or not _has_required_keys(table):
        raise RuntimeError("DynamoDB table has an incompatible key schema")
    if table.get("TableStatus") not in {"ACTIVE", "UPDATING"}:
        raise RuntimeError("DynamoDB table is unavailable at startup")

    # TTL performs cleanup; application reads and writes enforce expiry.
    # A TTL mismatch merits an operational warning, not traffic rejection.
    try:
        ttl_response = client.describe_time_to_live(TableName=table_name)
    except (BotoCoreError, ClientError):
        logger.warning(
            "DynamoDB startup warning category=ttl_unverified table=%s",
            table_name,
        )
        return
    if not _has_required_ttl(ttl_response):
        logger.warning(
            "DynamoDB startup warning category=ttl_contract table=%s",
            table_name,
        )


def _has_required_keys(table):
    keys = table.get("KeySchema")
    definitions = table.get("AttributeDefinitions")
    if not isinstance(keys, list) or not isinstance(definitions, list):
        return False
    key_pairs = set()
    for key in keys:
        if not isinstance(key, dict):
            return False
        name = key.get("AttributeName")
        kind = key.get("KeyType")
        if not isinstance(name, str) or not isinstance(kind, str):
            return False
        key_pairs.add((name, kind))
    if len(keys) != 2 or key_pairs != {("pk", "HASH"), ("sk", "RANGE")}:
        return False
    types = {}
    for definition in definitions:
        if not isinstance(definition, dict):
            return False
        name = definition.get("AttributeName")
        if not isinstance(name, str) or name in types:
            return False
        types[name] = definition.get("AttributeType")
    return types.get("pk") == "S" and types.get("sk") == "S"


def _has_required_ttl(response):
    description = response.get("TimeToLiveDescription") \
        if isinstance(response, dict) else None
    return (
        isinstance(description, dict)
        and description.get("TimeToLiveStatus") == "ENABLED"
        and description.get("AttributeName") == "ttl"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with dependency_lifespan(app):
        yield


async def _poll_dependency(probe: DynamoDBReadinessProbe):
    while True:
        await asyncio.sleep(PROBE_INTERVAL_SECONDS)
        await asyncio.to_thread(probe.probe_once)


@asynccontextmanager
async def dependency_lifespan(app: FastAPI):
    """Validate static contract, seed readiness, then poll periodically."""
    configure_dependencies(app)
    probe = getattr(app.state, "dynamodb_readiness_probe", None)
    task = asyncio.create_task(_poll_dependency(probe)) if probe else None
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
