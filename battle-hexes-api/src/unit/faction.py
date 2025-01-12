class Faction:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
