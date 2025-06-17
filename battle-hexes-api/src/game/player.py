from pydantic import BaseModel
from enum import Enum
from typing import List
from src.unit.faction import Faction


class PlayerType(Enum):
    HUMAN = "Human"
    CPU = "Computer"


class Player(BaseModel):
    name: str
    type: PlayerType
    factions: List[Faction]

    def has_faction(self, faction: Faction) -> bool:
        return faction in self.factions

    def owns(self, unit) -> bool:
        return unit.faction in self.factions

    def own_units(self, units) -> List:
        return [unit for unit in units if self.owns(unit)]
