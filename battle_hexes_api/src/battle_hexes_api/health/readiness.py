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
            response = client.describe_table(
                TableName=self.config.table_name,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("DynamoDB readiness check failed: %s", exc)
            return False

        status = response.get("Table", {}).get("TableStatus")
        if status != "ACTIVE":
            logger.warning(
                "DynamoDB readiness check found table status %r", status
            )
            return False
        return True


def configure_readiness(app: FastAPI) -> None:
    """Validate, log, and install the application's readiness checker."""
    config = DynamoDBConfig.from_environment()
    if config.enabled:
        logger.info("DynamoDB dependency: enabled")
        logger.info("DynamoDB table: %s", config.table_name)
    else:
        logger.info("DynamoDB dependency: disabled")
        if config.table_name is not None:
            logger.warning(
                "DDB_TABLE_NAME is configured but DynamoDB is disabled"
            )
    app.state.readiness_checker = ReadinessChecker(config)


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
