"""Game-level Pydantic schemas."""

from typing import List, TYPE_CHECKING
import uuid

from pydantic import BaseModel, ConfigDict

from battle_hexes_core.game.player import Player

from .board import BoardModel

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.game import Game


class GameModel(BaseModel):
    """Serialized representation of the core ``Game`` object."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: uuid.UUID
    players: List[Player]
    board: BoardModel

    @classmethod
    def from_game(cls, game: "Game") -> "GameModel":
        """Create a ``GameModel`` instance from the core ``Game`` object."""

        return cls(
            id=game.get_id(),
            players=list(game.get_players()),
            board=BoardModel.from_board(game.get_board()),
        )
