"""Adapters for combat resolution and turn transition."""

from dataclasses import dataclass

from battle_hexes_core.combat.combat import Combat
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from .common import notify_game_completion, reject_completed_game
from battle_hexes_api.ppo_state import capture_rng, is_ppo_game
from battle_hexes_api.ppo_human import check_human_board, require_human


@dataclass(frozen=True)
class CombatCommandResult:
    """Already-computed combat values needed by response serialization."""

    combat_results: object


class CombatAdapter:
    """Synchronize the board, resolve combat once, and score its result."""

    def __init__(
        self,
        sparse_board,
        combat_factory=Combat,
        scorer_factory=ObjectiveScorer,
    ):
        self._sparse_board = sparse_board
        self._combat_factory = combat_factory
        self._scorer_factory = scorer_factory

    def __call__(self, game):
        reject_completed_game(game)
        require_human(game, "combat")
        if is_ppo_game(game):
            check_human_board(game, self._sparse_board)
        self._sparse_board.apply_to_board(game.get_board())
        combat = (self._combat_factory(game, rng=game.ppo_rng)
                  if is_ppo_game(game) else self._combat_factory(game))
        results = combat.resolve_combat()
        game.end_combat()
        scorer = self._scorer_factory()
        scorer.award_hold_objectives_after_combat(game, results)
        scorer.recalculate_scenario_victory(game)
        if game.get_game_status().state == "completed":
            game.end_turn()
        capture_rng(game)
        notify_game_completion(game)
        return CombatCommandResult(results)


class EndTurnAdapter:
    """Synchronize state, update victory, and advance the turn."""

    def __init__(self, sparse_board, scorer_factory=ObjectiveScorer):
        self._sparse_board = sparse_board
        self._scorer_factory = scorer_factory

    def __call__(self, game):
        reject_completed_game(game)
        require_human(game, "end_turn")
        if is_ppo_game(game):
            check_human_board(game, self._sparse_board)
        self._sparse_board.apply_to_board(game.get_board())
        self._scorer_factory().recalculate_scenario_victory(game)
        game.end_turn()
        if is_ppo_game(game):
            game.ppo_state["pending_unit_ids"] = (
                [unit.id for unit in game.board.get_units_for_player(
                    game.players[0])]
                if game.current_player is game.players[0] else [])
            capture_rng(game)
        notify_game_completion(game)
        return None
