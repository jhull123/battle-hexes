"""Pydantic models for player type information returned by the API."""

from __future__ import annotations

from .api_model import ApiBaseModel

from battle_hexes_api.player_types import PlayerTypeDefinition


class PlayerTypeModel(ApiBaseModel):
    """Serialize player type definitions for API responses."""

    id: str
    name: str

    @classmethod
    def from_definition(
        cls, definition: PlayerTypeDefinition
    ) -> "PlayerTypeModel":
        """Create a :class:`PlayerTypeModel` from a definition dataclass."""

        return cls(id=definition.id, name=definition.name)
