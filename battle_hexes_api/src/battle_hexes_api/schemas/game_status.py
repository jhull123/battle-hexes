"""API schema for backend-computed game status."""

from __future__ import annotations

from typing import Literal

from .api_model import ApiBaseModel


class GameStatus(ApiBaseModel):
    """Serialized game completion status."""

    state: Literal["in_progress", "completed"]
    winner_player_name: str | None = None
    winner_faction_id: str | None = None
    reason: str | None = None
    message: str | None = None

    @classmethod
    def from_core(cls, status) -> "GameStatus":
        return cls(
            state=status.state,
            winner_player_name=status.winner_player_name,
            winner_faction_id=status.winner_faction_id,
            reason=status.reason,
            message=status.message,
        )
