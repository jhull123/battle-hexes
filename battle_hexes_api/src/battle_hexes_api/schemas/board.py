"""Board-related Pydantic schemas used by the API."""

from typing import List, TYPE_CHECKING

from pydantic import BaseModel

from .unit import UnitModel

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.board import Board


class BoardModel(BaseModel):
    """Serialized representation of the in-memory board."""

    rows: int
    columns: int
    units: List[UnitModel]

    @classmethod
    def from_board(cls, board: "Board") -> "BoardModel":
        """Create a ``BoardModel`` from the core ``Board`` instance."""

        units = [UnitModel.from_unit(unit) for unit in board.get_units()]
        return cls(
            rows=board.get_rows(),
            columns=board.get_columns(),
            units=units,
        )
