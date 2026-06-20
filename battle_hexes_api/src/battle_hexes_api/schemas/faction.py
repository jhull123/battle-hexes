"""Pydantic schema for faction resources."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from .api_model import ApiBaseModel, to_camel, to_snake

from battle_hexes_core.unit.faction import Faction


class FactionModel(ApiBaseModel):
    """Pydantic representation of the core :class:`Faction`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    color: str
    sounds: dict = Field(default_factory=dict)

    @classmethod
    def from_core(cls, faction: Faction) -> "FactionModel":
        """Create a ``FactionModel`` from a core :class:`Faction`."""

        return cls(
            id=faction.id,
            name=faction.name,
            color=faction.color,
            sounds=cls._camelize_sound_keys(faction.sounds),
        )

    def to_core(self) -> Faction:
        """Convert the Pydantic model back into a core :class:`Faction`."""

        return Faction(
            id=self.id,
            name=self.name,
            color=self.color,
            sounds=self._snakeize_sound_keys(self.sounds),
        )

    @classmethod
    def _camelize_sound_keys(cls, value):
        """Convert scenario-authored sound keys to the API casing contract."""

        return cls._convert_sound_keys(value, to_camel)

    @classmethod
    def _snakeize_sound_keys(cls, value):
        """Convert API sound keys back to the core scenario casing."""

        return cls._convert_sound_keys(value, to_snake)

    @classmethod
    def _convert_sound_keys(cls, value, converter):
        if isinstance(value, dict):
            return {
                converter(key) if isinstance(key, str) else key:
                cls._convert_sound_keys(nested_value, converter)
                for key, nested_value in value.items()
            }
        if isinstance(value, list):
            return [
                cls._convert_sound_keys(nested_value, converter)
                for nested_value in value
            ]
        return value
