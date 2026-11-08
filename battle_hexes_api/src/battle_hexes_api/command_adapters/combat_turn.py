"""Adapters for combat resolution and turn transition."""

from dataclasses import dataclass

from battle_hexes_core.combat.combat import Combat
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer
from battle_hexes_api.agent_integrations import integrations

from .common import notify_game_completion, reject_completed_game


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
        agent_integrations=integrations,
    ):
        self._sparse_board = sparse_board
        self._combat_factory = combat_factory
        self._scorer_factory = scorer_factory
        self._integrations = agent_integrations

    def __call__(self, game):
        reject_completed_game(game)
        integration = self._integrations.for_game(game)
        integration.authorize(game, "combat", self._sparse_board)
        self._sparse_board.apply_to_board(game.get_board())
        rng = integration.combat_rng(game)
        combat = (self._combat_factory(game) if rng is None else
                  self._combat_factory(game, rng=rng))
        results = combat.resolve_combat()
        game.end_combat()
        scorer = self._scorer_factory()
        scorer.award_hold_objectives_after_combat(game, results)
        scorer.recalculate_scenario_victory(game)
        if game.get_game_status().state == "completed":
            game.end_turn()
        integration.capture_rng(game)
        notify_game_completion(game)
        return CombatCommandResult(results)


class EndTurnAdapter:
    """Synchronize state, update victory, and advance the turn."""

    def __init__(self, sparse_board, scorer_factory=ObjectiveScorer,
                 agent_integrations=integrations):
        self._sparse_board = sparse_board
        self._scorer_factory = scorer_factory
        self._integrations = agent_integrations

    def __call__(self, game):
        reject_completed_game(game)
        integration = self._integrations.for_game(game)
        integration.authorize(game, "end-turn", self._sparse_board)
        self._sparse_board.apply_to_board(game.get_board())
        self._scorer_factory().recalculate_scenario_victory(game)
        game.end_turn()
        integration.after_end_turn(game)
        notify_game_completion(game)
        return None
