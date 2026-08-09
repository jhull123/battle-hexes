"""Schemas for movement responses and defensive-fire events."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .api_model import ApiBaseModel

from .game_model import GameModel
from .sparseboard import SparseBoard


class DefensiveFireEventModel(ApiBaseModel):
    """Serialized defensive-fire event emitted during movement."""

    firing_unit_id: str
    target_unit_id: str
    trigger_hex: tuple[int, int]
    target_hex_before: tuple[int, int]
    outcome: str
    retreat_destination: tuple[int, int] | None = None
    spent_defensive_fire: bool = True
    probability: float | None = None
    roll: float | None = None
    message: str

    @classmethod
    def from_result(cls, result: Any) -> "DefensiveFireEventModel":
        """Build a schema instance from a core defensive-fire result."""

        return cls(
            firing_unit_id=result.firing_unit_id,
            target_unit_id=result.target_unit_id,
            trigger_hex=result.trigger_hex,
            target_hex_before=result.target_hex_before,
            outcome=result.outcome,
            retreat_destination=result.retreat_destination,
            spent_defensive_fire=result.spent_defensive_fire,
            probability=result.probability,
            roll=result.roll,
            message=cls._message_for(result),
        )

    @staticmethod
    def _message_for(result: Any) -> str:
        if result.outcome == "retreat":
            if result.retreat_destination is None:
                return (
                    "Defensive fire eliminated the target during retreat."
                )
            return (
                "Defensive fire forced the target to retreat to "
                f"{result.retreat_destination}."
            )
        return "Defensive fire had no effect."


class MovementPathHexModel(ApiBaseModel):
    """Coordinate in a serialized movement path."""

    row: int
    column: int


class MovementPlanModel(ApiBaseModel):
    """Serialized unit movement plan."""

    unit_id: str
    path: list[MovementPathHexModel] = Field(default_factory=list)

    @classmethod
    def from_plan(cls, plan: Any) -> "MovementPlanModel":
        """Build a movement plan schema from a core movement plan."""

        return cls.model_validate(plan.to_dict())


class MovementResponseModel(ApiBaseModel):
    """Movement endpoint payload including board updates and reactions."""

    game: GameModel
    plans: list[MovementPlanModel] = Field(default_factory=list)
    sparse_board: SparseBoard
    defensive_fire_events: list[DefensiveFireEventModel] = Field(
        default_factory=list
    )
    scores: dict[str, int] = Field(default_factory=dict)
    turn_limit: int | None = None
    turn_number: int = 1

    @classmethod
    def from_movement_result(
        cls,
        game: Any,
        plans: list[Any],
        movement_resolution: Any,
    ) -> "MovementResponseModel":
        """Build a response model from a core game and movement result."""

        defensive_fire_results = getattr(
            movement_resolution,
            "defensive_fire_results",
            [],
        )
        sparse_board = SparseBoard.from_game(
            game,
            game_status=getattr(movement_resolution, "game_status", None),
        )
        return cls(
            game=GameModel.from_game(game),
            plans=[MovementPlanModel.from_plan(plan) for plan in plans],
            sparse_board=sparse_board,
            defensive_fire_events=[
                DefensiveFireEventModel.from_result(result)
                for result in defensive_fire_results
            ],
            scores=game.get_score_tracker().get_scores(),
            turn_limit=getattr(game, "turn_limit", None),
            turn_number=getattr(game, "turn_number", 1),
        )
