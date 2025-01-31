from pydantic import BaseModel
import uuid
from src.unit.faction import Faction


class UnitModel(BaseModel):
    id: uuid.UUID
    name: str
    faction_id: uuid.UUID
    type: str
    attack: int
    defense: int
    move: int
    row: int
    column: int


class Unit:
    def __init__(self, id: uuid.UUID, name: str, faction: Faction, type: str,
                 attack: int, defense: int, move: int,
                 row: int = None, column: int = None):
        self.id = id
        self.name = name
        self.faction = faction
        self.type = type
        self.attack = attack
        self.defense = defense
        self.move = move
        self.row = row
        self.column = column

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_faction(self):
        return self.faction

    def get_type(self):
        return self.type

    def get_attack(self):
        return self.attack

    def get_defense(self):
        return self.defense

    def get_move(self):
        return self.move

    def set_coords(self, row, column):
        self.row = row
        self.column = column

    def get_coords(self):
        return (self.row, self.column)

    def to_unit_model(self) -> UnitModel:
        return UnitModel(id=self.id,
                         name=self.name,
                         faction_id=self.faction.id,
                         type=self.type,
                         attack=self.attack,
                         defense=self.defense,
                         move=self.move,
                         row=self.row,
                         column=self.column)

    def __str__(self):
        return f"{self.name} ({self.faction.get_name()})", \
               f"{self.attack}-{self.defense}-{self.move}"
