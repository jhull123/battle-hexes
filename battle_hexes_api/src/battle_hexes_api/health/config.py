"""Validated runtime configuration for the optional DynamoDB dependency."""

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class DynamoDBConfig:
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
