class Hex:
    def __init__(self, row: int, column: int):
        self._row = row
        self._column = column

    @property
    def row(self) -> int:
        return self._row

    @property
    def column(self) -> int:
        return self._column

    def __eq__(self, other):
        if not isinstance(other, Hex):
            return False
        return self.row == other.row and self.column == other.column

    def __hash__(self):
        return hash((self.row, self.column))

    def __str__(self):
        return f"({self.row}, {self.column})"

    def __repr__(self):
        return f"Hex({self.row}, {self.column})"
