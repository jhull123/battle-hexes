"""Game-level Pydantic schemas."""

from typing import List
import uuid

from pydantic import BaseModel, ConfigDict

from battle_hexes_core.game.player import Player

from .board import BoardModel


class GameModel(BaseModel):
    """Serialized representation of the core ``Game`` object."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: uuid.UUID
    players: List[Player]
    board: BoardModel
