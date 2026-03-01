class Terrain:
    def __init__(self, name: str, hex_color: str, move_cost: int = 1):
        self._name = name
        self._hex_color = hex_color
        self._move_cost = move_cost

    @property
    def name(self) -> str:
        return self._name

    @property
    def hex_color(self) -> str:
        return self._hex_color

    @property
    def move_cost(self) -> int:
        return self._move_cost

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Terrain({self.name})"
