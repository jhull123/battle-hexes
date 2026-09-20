"""Pure response serializers paired with authoritative game commands."""

from battle_hexes_core.scenario.scenario_loader import load_scenario

from battle_hexes_api.schemas import (
    GameModel,
    MovementResponseModel,
    SparseBoard,
)
from battle_hexes_api.schemas.api_model import api_model_json_bytes


def _response(model):
    return 200, api_model_json_bytes(model), "application/json", {}


class GameResponseSerializer:
    """Serialize a full-game projection with supplied persistence metadata."""

    def __init__(
        self,
        scenario_version,
        scenario_loader=None,
    ):
        self._scenario_version = scenario_version
        self._scenario_loader = scenario_loader

    def __call__(self, game, _operation_result, resulting_version):
        scenario = None
        if self._scenario_loader is not None:
            scenario = self._scenario_loader(game.scenario_id)
        return _response(GameModel.from_game(
            game,
            scenario,
            game_version=resulting_version,
            scenario_version=self._scenario_version,
        ))


class CreateGameResponseSerializer(GameResponseSerializer):
    """Serialize creation with static scenario display information."""

    def __init__(self, scenario_version, scenario_loader=load_scenario):
        super().__init__(scenario_version, scenario_loader)


class MovementResponseSerializer:
    """Serialize movement without executing any game behavior."""

    def __init__(self, scenario_version):
        self._scenario_version = scenario_version

    def __call__(self, game, result, resulting_version):
        model = MovementResponseModel.from_movement_result(
            game,
            list(result.plans),
            result.movement_resolution,
            game_version=resulting_version,
            scenario_version=self._scenario_version,
        )
        return _response(model)


class CombatResponseSerializer:
    """Serialize the sparse board and an already-resolved combat result."""

    def __call__(self, game, result, resulting_version):
        model = SparseBoard.from_game(
            game,
            include_scores=True,
            combat_results=result.combat_results,
            game_version=resulting_version,
        )
        return _response(model)


class EndTurnResponseSerializer(GameResponseSerializer):
    """Serialize the full game after its turn transition."""
