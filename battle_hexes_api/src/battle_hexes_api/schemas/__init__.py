"""Pydantic schemas for the Battle Hexes API."""

from .board import BoardModel
from .combat import CombatResultSchema
from .create_game import CreateGameRequest
from .faction import FactionModel
from .game_model import GameModel
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
    "GameModel",
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
