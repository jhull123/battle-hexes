"""Camel-case projection of an already-resolved PPO order."""

from .api_model import ApiBaseModel
from .game_log import CombatEventModel
from .game_model import GameModel, PpoTurnModel
from .movement import DefensiveFireEventModel, MovementPlanModel
from battle_hexes_core.scenario.scenario_loader import load_scenario
from battle_agent_rl.ppo.playable_scenario import SCENARIO_VERSION


class PpoOrderResponse(ApiBaseModel):
    game_version: int
    game: GameModel
    ppo_turn: PpoTurnModel
    plan: MovementPlanModel
    defensive_fire_events: list[DefensiveFireEventModel]
    combat_events: list[CombatEventModel]

    @classmethod
    def from_result(cls, game, result, version):
        from dataclasses import asdict
        projection = GameModel.from_game(
            game, load_scenario(game.scenario_id), game_version=version,
            scenario_version=SCENARIO_VERSION)
        return cls(
            game_version=version, game=projection,
            ppo_turn=projection.ppo_turn,
            plan=MovementPlanModel.from_plan(result.plan),
            defensive_fire_events=[DefensiveFireEventModel.from_result(event)
                                   for event in result.fire],
            combat_events=[CombatEventModel.model_validate(asdict(event))
                           for event in result.combats],
        )
