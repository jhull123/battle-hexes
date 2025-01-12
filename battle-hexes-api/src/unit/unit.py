from src.unit.faction import Faction


class Unit:
    def __init__(self, faction: Faction):
        self.row = None
        self.column = None
        self.faction = faction

    def get_faction(self):
        return self.faction

    def set_coords(self, row, column):
        self.row = row
        self.column = column

    def get_coords(self):
        return (self.row, self.column)
