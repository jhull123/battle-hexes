class Terrain:
    def __init__(
        self,
        name: str,
        hex_color: str,
        move_cost: int = 1,
        defensive_fire_modifier: float = 1.0,
    ):
        self._name = name
        self._hex_color = hex_color
        self._move_cost = move_cost
        self._defensive_fire_modifier = defensive_fire_modifier

    @property
    def name(self) -> str:
        return self._name

    @property
    def hex_color(self) -> str:
        return self._hex_color

    @property
    def move_cost(self) -> int:
        return self._move_cost

    @property
    def defensive_fire_modifier(self) -> float:
        return self._defensive_fire_modifier

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Terrain({self.name})"
