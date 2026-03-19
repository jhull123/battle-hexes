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
    echelon: str | None = None
    defense: int
    move: int
    row: int
    column: int
    defensive_fire_available: bool = True

    @classmethod
    def from_unit(cls, unit: "Unit") -> "UnitModel":
        """Create a unit model from a core :class:`Unit`."""

        return cls(
            id=str(unit.id),
            name=unit.name,
            faction_id=unit.faction.id,
            type=unit.type,
            attack=unit.attack,
            echelon=unit.echelon,
            defense=unit.defense,
            move=unit.move,
            row=unit.row,
            column=unit.column,
            defensive_fire_available=unit.has_defensive_fire(),
        )


class SparseUnit(BaseModel):
    """Model representing a unit's minimal state for position updates."""
    id: str
    row: int
    column: int
    defensive_fire_available: bool | None = None

    @classmethod
    def from_unit(cls, unit: "Unit") -> "SparseUnit":
        """Create a sparse unit model from a core :class:`Unit`."""

        return cls(
            id=str(unit.id),
            row=unit.row,
            column=unit.column,
            defensive_fire_available=unit.has_defensive_fire(),
        )
