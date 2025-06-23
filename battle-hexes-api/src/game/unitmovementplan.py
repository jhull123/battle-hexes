from typing import List, Any
from src.game.hex import Hex


class UnitMovementPlan:
    def __init__(self, unit: Any, path: List[Hex]):
        self.unit = unit
        self.path = path

    def __repr__(self):
        return f"UnitMovementPlan(unit={self.unit}, path={self.path})"
