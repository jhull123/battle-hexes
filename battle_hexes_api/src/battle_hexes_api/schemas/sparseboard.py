"""Schemas describing sparse board representations."""

from typing import List, Optional

from pydantic import BaseModel

from battle_hexes_core.combat.combatresult import CombatResultSchema

from .unit import SparseUnit


class SparseBoard(BaseModel):
    """A lightweight representation of the game board used by the API."""

    units: List[SparseUnit] = []
    last_combat_results: Optional[List[CombatResultSchema]] = None

    def add_unit(self, unit: SparseUnit) -> None:
        self.units.append(unit)

    def get_units(self) -> List[SparseUnit]:
        return self.units
