from battle_hexes_core.game.terrain import Terrain


class Hex:
    def __init__(self, row: int, column: int, terrain: Terrain | None = None):
        self._row = row
        self._column = column
        self._terrain = terrain

    @property
    def row(self) -> int:
        return self._row

    @property
    def column(self) -> int:
        return self._column

    @property
    def terrain(self) -> Terrain:
        return self._terrain

    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.row == other[0] and self.column == other[1]
        if isinstance(other, Hex):
            return self.row == other.row and self.column == other.column
        return False

    def __hash__(self):
        return hash((self.row, self.column))

    def __str__(self):
        return f"({self.row}, {self.column}, {self.terrain})"

    def __repr__(self):
        return f"Hex({self.row}, {self.column}, {self.terrain})"
