"""Pydantic models for the create game request."""

from __future__ import annotations

from typing import List

from pydantic import Field, field_validator

from .api_model import ApiBaseModel


class CreateGameRequest(ApiBaseModel):
    """Request body for the ``POST /games`` endpoint."""

    scenario_id: str
    player_types: List[str] = Field(
        min_length=2, max_length=2,
        description="Identifiers for the desired player implementations.",
    )

    @field_validator("player_types")
    def _validate_player_types(cls, value: List[str]) -> List[str]:
        """Ensure each player type identifier is a non-empty string."""

        cleaned = [v.strip() for v in value if isinstance(v, str)]
        if len(cleaned) != len(value) or any(not v for v in cleaned):
            raise ValueError("Player types must be non-empty strings")
        return cleaned
