"""Pydantic schema for faction resources."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from battle_hexes_core.unit.faction import Faction


class FactionModel(BaseModel):
    """Pydantic representation of the core :class:`Faction`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    color: str

    @classmethod
    def from_core(cls, faction: Faction) -> "FactionModel":
        """Create a ``FactionModel`` from a core :class:`Faction`."""

        return cls.model_validate(faction)

    def to_core(self) -> Faction:
        """Convert the Pydantic model back into a core :class:`Faction`."""

        return Faction(id=self.id, name=self.name, color=self.color)
