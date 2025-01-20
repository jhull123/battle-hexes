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
