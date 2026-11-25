"""Private occupancy projection for sequential scripted movement plans."""

from copy import copy

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan


class MovementProjection:
    def __init__(self, board: Board):
        # Share the read-only map and reuse its movement rules. Copy the
        # occupancy mapping and copy individual units only when relocating.
        self.board = copy(board)
        self.board.units = board.units.copy()

    def accept(self, plan: UnitMovementPlan) -> None:
        unit = copy(plan.unit)
        destination = plan.path[-1]
        unit.set_coords(destination.row, destination.column)
        self.board.units[unit.get_id()] = unit
