from pydantic import BaseModel
from typing import List
from src.unit.sparseunit import SparseUnit


class SparseBoard(BaseModel):
    units: List[SparseUnit] = []

    def add_unit(self, unit: SparseUnit):
        self.units.append(unit)

    def get_units(self) -> List[SparseUnit]:
        return self.units
