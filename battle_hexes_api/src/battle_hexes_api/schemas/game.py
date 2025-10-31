"""Pydantic schema representations of core ``Game`` objects."""

from __future__ import annotations

from typing import List, TYPE_CHECKING
import uuid

from pydantic import BaseModel

from battle_hexes_core.game.board import BoardModel
from battle_hexes_core.game.player import Player

if TYPE_CHECKING:
    from battle_hexes_core.game.game import Game


class GameModel(BaseModel):
    """Serializable representation of a core ``Game`` instance."""

    id: uuid.UUID
    players: List[Player]
    board: BoardModel

    @classmethod
    def from_game(cls, game: "Game") -> "GameModel":
        """Create a ``GameModel`` instance from a ``Game`` object."""
        return cls(
            id=game.get_id(),
            players=game.get_players(),
            board=game.get_board().to_board_model(),
        )
