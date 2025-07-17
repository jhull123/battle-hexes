from typing import List, Any
from game.hex import Hex


class UnitMovementPlan:
    def __init__(self, unit: Any, path: List[Hex]):
        self.unit = unit
        self.path = path

    def __repr__(self):
        return f"UnitMovementPlan(unit={self.unit}, path={self.path})"

    def to_dict(self) -> dict:
        """Serialize this plan into a simple dictionary."""
        return {
            "unit_id": str(self.unit.get_id()),
            "path": [
                {"row": h.row, "column": h.column}
                for h in self.path
            ],
        }
