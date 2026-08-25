"""Game-level Pydantic schemas."""

from typing import List, TYPE_CHECKING
import uuid

from pydantic import ConfigDict, Field

from .api_model import ApiBaseModel

from .board import BoardModel
from .game_status import GameStatus
from .objective import ObjectiveModel
from .player import PlayerModel
from .reinforcement import ReinforcementsModel

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.game import Game
    from battle_hexes_core.scenario.scenario import Scenario


class GameModel(ApiBaseModel):
    """Serialized representation of the core ``Game`` object."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: uuid.UUID
    players: List[PlayerModel]
    board: BoardModel
    objectives: List[ObjectiveModel]
    scores: dict[str, int]
    turn_limit: int | None = None
    turn_number: int = 1
    scenario_id: str | None = None
    scenario_name: str | None = None
    stacking_limit: int | None = None
    player_type_ids: list[str] | None = None
    game_status: GameStatus | None = None
    active_player: str | None = None
    current_phase: str | None = None
    pending_combats: list[dict[str, list[str]]] = Field(default_factory=list)
    reinforcements: ReinforcementsModel | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @classmethod
    def from_game(
        cls, game: "Game", scenario: "Scenario | None" = None
    ) -> "GameModel":
        """Create a ``GameModel`` instance from the core ``Game`` object."""

        return cls(
            id=game.get_id(),
            players=[
                PlayerModel.from_core(player)
                for player in game.get_players()
            ],
            board=BoardModel.from_board(game.get_board(), scenario),
            objectives=[
                ObjectiveModel.from_objective(objective)
                for objective in game.get_board().get_objectives()
            ],
            scores=game.get_score_tracker().get_scores(),
            turn_limit=getattr(game, "turn_limit", None),
            turn_number=getattr(game, "turn_number", 1),
            scenario_id=getattr(game, "scenario_id", None),
            scenario_name=getattr(scenario, "name", None),
            stacking_limit=getattr(scenario, "stacking_limit", None),
            player_type_ids=getattr(game, "player_type_ids", None),
            game_status=GameStatus.from_core(game.get_game_status()),
            active_player=getattr(game.get_current_player(), "name", None),
            current_phase=getattr(game, "current_phase", None),
            pending_combats=getattr(game, "pending_combats", []),
            reinforcements=ReinforcementsModel.from_game(game),
        )
