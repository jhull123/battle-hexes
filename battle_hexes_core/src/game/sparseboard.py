from pydantic import BaseModel
from typing import List, Optional
from combat.combatresult import CombatResultSchema
from unit.sparseunit import SparseUnit


class SparseBoard(BaseModel):
    units: List[SparseUnit] = []
    last_combat_results: Optional[List[CombatResultSchema]] = None

    def add_unit(self, unit: SparseUnit):
        self.units.append(unit)

    def get_units(self) -> List[SparseUnit]:
        return self.units
