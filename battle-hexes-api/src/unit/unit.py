from src.unit.faction import Faction


class Unit:
    def __init__(self, name: str, faction: Faction, type: str, attack: int,
                 defense: int, move: int):
        self.row = None
        self.column = None
        self.name = name
        self.faction = faction
        self.type = type
        self.attack = attack
        self.defense = defense
        self.move = move

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
