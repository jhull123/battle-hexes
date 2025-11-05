"""Pydantic models for the create game request."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateGameRequest(BaseModel):
    """Request body for the ``POST /games`` endpoint."""

    scenario_id: str = Field(alias="scenarioId")
    player_types: List[str] = Field(
        alias="playerTypes", min_length=2, max_length=2,
        description="Identifiers for the desired player implementations.",
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("player_types")
    def _validate_player_types(cls, value: List[str]) -> List[str]:
        """Ensure each player type identifier is a non-empty string."""

        cleaned = [v.strip() for v in value if isinstance(v, str)]
        if len(cleaned) != len(value) or any(not v for v in cleaned):
            raise ValueError("Player types must be non-empty strings")
        return cleaned
