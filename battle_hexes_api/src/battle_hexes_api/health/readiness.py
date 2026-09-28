"""Liveness and current dependency availability endpoints."""

import logging
from typing import Callable

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Request

from .config import DynamoDBConfig

logger = logging.getLogger(__name__)
router = APIRouter()


class ReadinessChecker:
    """Check whether the configured DynamoDB table can serve requests."""

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
            response = self.client_factory().describe_table(
                TableName=self.config.table_name,
            )
        except (BotoCoreError, ClientError):
            logger.warning(
                "DynamoDB readiness failure category=provider_error table=%s",
                self.config.table_name,
            )
            return False

        table = response.get("Table") if isinstance(response, dict) else None
        # DynamoDB permits data operations while a table is UPDATING.
        if not isinstance(table, dict) or table.get("TableStatus") not in {
            "ACTIVE", "UPDATING"
        }:
            logger.warning(
                "DynamoDB readiness failure category=table_unavailable "
                "table=%s",
                self.config.table_name,
            )
            return False
        return True


@router.get("/health")
def health():
    """Report process liveness without contacting AWS."""
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request):
    """Report whether the configured dependency is currently available."""
    if not request.app.state.readiness_checker.is_ready():
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}
