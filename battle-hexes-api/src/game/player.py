from enum import Enum


class PlayerType(Enum):
    HUMAN = "Human"
    CPU = "Computer"


class Player:
    def __init__(self, name: str, type: PlayerType, factions: list):
        self.name = name
        self.type = type
        self.factions = factions

    def get_name(self):
        return self.name

    def get_type(self):
        return self.type
