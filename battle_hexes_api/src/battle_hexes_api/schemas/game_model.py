"""Game-level Pydantic schemas."""

from typing import List, TYPE_CHECKING
import uuid

from pydantic import BaseModel, ConfigDict

from battle_hexes_core.game.player import Player

from .board import BoardModel
from .objective import ObjectiveModel

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.game import Game
    from battle_hexes_core.scenario.scenario import Scenario


class GameModel(BaseModel):
    """Serialized representation of the core ``Game`` object."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: uuid.UUID
    players: List[Player]
    board: BoardModel
    objectives: List[ObjectiveModel]

    @classmethod
    def from_game(
        cls, game: "Game", scenario: "Scenario | None" = None
    ) -> "GameModel":
        """Create a ``GameModel`` instance from the core ``Game`` object."""

        return cls(
            id=game.get_id(),
            players=list(game.get_players()),
            board=BoardModel.from_board(game.get_board(), scenario),
            objectives=[
                ObjectiveModel.from_objective(objective)
                for objective in game.get_board().get_objectives()
            ],
        )
