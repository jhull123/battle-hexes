"""Pydantic schemas for the Battle Hexes API."""

from .board import BoardModel
from .combat import CombatResultSchema
from .create_game import CreateGameRequest
from .faction import FactionModel
from .movement import DefensiveFireEventModel, MovementResponseModel
from .game_model import GameModel
from .game_status import GameStatus
from .objective import ObjectiveModel
from .player import PlayerModel
from .player_type import PlayerTypeModel
from .scenario import ScenarioModel
from .sparseboard import SparseBoard
from .terrain import TerrainHexModel, TerrainSummaryModel, TerrainTypeModel
from .unit import UnitModel, SparseUnit

__all__ = [
    "BoardModel",
    "CombatResultSchema",
    "CreateGameRequest",
    "FactionModel",
    "DefensiveFireEventModel",
    "GameModel",
    "GameStatus",
    "MovementResponseModel",
    "ObjectiveModel",
    "PlayerModel",
    "PlayerTypeModel",
    "ScenarioModel",
    "SparseBoard",
    "TerrainHexModel",
    "TerrainSummaryModel",
    "TerrainTypeModel",
    "UnitModel",
    "SparseUnit",
]
