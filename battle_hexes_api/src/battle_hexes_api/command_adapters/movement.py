"""Adapters for movement-phase game commands."""

from dataclasses import dataclass

from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from .common import notify_game_completion, reject_completed_game


@dataclass(frozen=True)
class MovementCommandResult:
    """Already-computed movement values needed by response serialization."""

    plans: tuple
    movement_resolution: object


def _apply_plans(game, plans) -> MovementCommandResult:
    plans = tuple(plans)
    resolution = game.apply_movement_plans(plans)
    return MovementCommandResult(plans, resolution)


class MovementAdapter:
    """Obtain and execute the current player's movement plans."""

    def __call__(self, game):
        reject_completed_game(game)
        result = _apply_plans(game, game.get_current_player().movement())
        notify_game_completion(game)
        return result


class HumanMoveAdapter:
    """Convert and execute a submitted sparse-board movement."""

    def __init__(self, sparse_board):
        self._sparse_board = sparse_board

    def __call__(self, game):
        reject_completed_game(game)
        plans = self._sparse_board.to_movement_plans(game.get_board())
        result = _apply_plans(game, plans)
        notify_game_completion(game)
        return result


class EndMovementAdapter:
    """Apply final movement, score objectives, and enter the next phase."""

    def __init__(self, sparse_board, scorer_factory=ObjectiveScorer):
        self._sparse_board = sparse_board
        self._scorer_factory = scorer_factory

    def __call__(self, game):
        reject_completed_game(game)
        plans = self._sparse_board.to_movement_plans(game.get_board())
        result = _apply_plans(game, plans)
        self._scorer_factory().award_hold_objectives(game)
        game.end_movement()
        notify_game_completion(game)
        return result
