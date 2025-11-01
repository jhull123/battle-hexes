"""Schemas describing sparse board representations."""

from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from battle_hexes_core.combat.combatresult import CombatResultSchema

from .unit import SparseUnit

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.board import Board


class SparseBoard(BaseModel):
    """A lightweight representation of the game board used by the API."""

    units: List[SparseUnit] = Field(default_factory=list)
    last_combat_results: Optional[List[CombatResultSchema]] = None

    def add_unit(self, unit: SparseUnit) -> None:
        self.units.append(unit)

    def get_units(self) -> List[SparseUnit]:
        return self.units

    @classmethod
    def from_board(cls, board: "Board") -> "SparseBoard":
        """Create a ``SparseBoard`` from the provided ``Board``."""

        units = [SparseUnit.from_unit(unit) for unit in board.get_units()]
        return cls(units=units)

    def apply_to_board(self, board: "Board") -> None:
        """Update ``board`` to match the data contained in this schema."""

        for unit_data in self.units:
            unit_id = str(unit_data.id)
            unit = board.get_unit_by_id(unit_id)
            unit.set_coords(unit_data.row, unit_data.column)
