from pydantic import BaseModel
from uuid import UUID
from typing import List
from src.game.sparseboard import SparseBoard
from src.unit.unit import Unit, UnitModel


class BoardModel(BaseModel):
    rows: int
    columns: int
    units: List[UnitModel]


class Board:
    def __init__(self, rows: int, columns: int):
        self.rows = rows
        self.columns = columns
        self.units: dict[UUID, Unit] = {}

    def get_rows(self) -> int:
        return self.rows

    def get_columns(self) -> int:
        return self.columns

    def add_unit(self, unit: Unit, row: int, column: int) -> None:
        if not (0 <= row < self.rows) or not (0 <= column < self.columns):
            raise ValueError("Unit is out of bounds")

        unit.set_coords(row, column)
        self.units[unit.get_id()] = unit

    def get_units(self) -> List[Unit]:
        return list(self.units.values())

    def get_unit_by_id(self, unit_id: UUID) -> Unit:
        if not isinstance(unit_id, UUID):
            unit_id = UUID(unit_id)
        unit = self.units.get(unit_id)
        if not unit:
            raise KeyError(f"No unit found with ID {unit_id}")
        return unit

    def update(self, sparse_board: SparseBoard) -> None:
        for unit_data in sparse_board.units:
            unit_id = unit_data.id
            if isinstance(unit_id, str):
                unit_id = UUID(unit_id)
            unit = self.get_unit_by_id(unit_id)
            unit.set_coords(unit_data.row, unit_data.column)

    def to_board_model(self) -> BoardModel:
        units = [unit.to_unit_model() for unit in self.get_units()]
        return BoardModel(rows=self.rows, columns=self.columns, units=units)
