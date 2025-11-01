"""Pydantic models for unit entities."""

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from battle_hexes_core.unit.unit import Unit


class UnitModel(BaseModel):
    """Model representing a unit's complete state."""
    id: str
    name: str
    faction_id: str
    type: str
    attack: int
    defense: int
    move: int
    row: int
    column: int

    @classmethod
    def from_unit(cls, unit: "Unit") -> "UnitModel":
        """Create a unit model from a core :class:`Unit`."""

        return cls(
            id=str(unit.id),
            name=unit.name,
            faction_id=unit.faction.id,
            type=unit.type,
            attack=unit.attack,
            defense=unit.defense,
            move=unit.move,
            row=unit.row,
            column=unit.column,
        )


class SparseUnit(BaseModel):
    """Model representing a unit's minimal state for position updates."""
    id: str
    row: int
    column: int

    @classmethod
    def from_unit(cls, unit: "Unit") -> "SparseUnit":
        """Create a sparse unit model from a core :class:`Unit`."""

        return cls(id=str(unit.id), row=unit.row, column=unit.column)
