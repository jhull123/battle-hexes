from typing import List
from pydantic import PrivateAttr
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan


class RLPlayer(Player):
    """Simple reinforcement learning player that performs no actions."""

    _board: Board = PrivateAttr()

    def __init__(self, name: str, type, factions, board: Board):
        super().__init__(name=name, type=type, factions=factions)
        self._board = board

    def movement(self) -> List[UnitMovementPlan]:
        """Return an empty list of movement plans."""
        return []
