"""Schemas describing sparse board representations."""

from typing import List, Optional, TYPE_CHECKING

from battle_hexes_core.game.movement import MovementCalculator

from pydantic import BaseModel, Field

from .combat import CombatResultSchema

from .unit import SparseUnit

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.board import Board


class SparseBoard(BaseModel):
    """A lightweight representation of the game board used by the API."""

    units: List[SparseUnit] = Field(default_factory=list)
    last_combat_results: Optional[List[CombatResultSchema]] = None
    scores: Optional[dict[str, int]] = None

    def add_unit(self, unit: SparseUnit) -> None:
        self.units.append(unit)

    def get_units(self) -> List[SparseUnit]:
        return self.units

    @classmethod
    def from_board(cls, board: "Board") -> "SparseBoard":
        """Create a ``SparseBoard`` from the provided ``Board``."""

        units = [SparseUnit.from_unit(unit) for unit in board.get_units()]
        return cls(units=units)

    def apply_to_board(self, board: "Board") -> None:
        """Update ``board`` to match the data contained in this schema."""

        movement = MovementCalculator(board)
        for unit_data in self.units:
            unit_id = str(unit_data.id)
            unit = board.get_unit_by_id(unit_id)
            self._sync_movement_points_remaining(
                board,
                movement,
                unit,
                unit_data.row,
                unit_data.column,
            )
            unit.set_coords(unit_data.row, unit_data.column)

    def _sync_movement_points_remaining(
        self,
        board: "Board",
        movement: MovementCalculator,
        unit,
        target_row: int,
        target_column: int,
    ) -> None:
        current_coords = unit.get_coords()
        if current_coords is None:
            return

        target_coords = (target_row, target_column)
        if current_coords == target_coords:
            return

        start_hex = board.get_hex(*current_coords)
        target_hex = board.get_hex(target_row, target_column)
        path = board.shortest_path(unit, start_hex, target_hex)
        movement_points_spent = 0
        for from_hex, to_hex in zip(path, path[1:]):
            movement_points_spent += movement.move_cost(unit, from_hex, to_hex)
        unit.current_turn_movement_points_remaining = max(
            unit.get_move() - movement_points_spent,
            0,
        )
