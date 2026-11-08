"""Shared live-plan execution and ordinary core phase/scoring transitions."""

from battle_hexes_core.combat.combat import Combat
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer


def finish_side(game, rng, *, score_objectives=False):
    """Close movement, resolve applicable combat once, then end through core.

    Legacy 07 callers retain their unscored contract. Scenario environments
    request ordinary-game scoring; no encoder owns scoring or completion.
    """
    scorer = ObjectiveScorer() if score_objectives else None
    if scorer:
        scorer.award_hold_objectives(game)
    if game.finalize_completed_phase():
        return
    game.end_movement()
    if game.current_phase == "combat":
        results = Combat(game, rng=rng).resolve_combat()
        game.end_combat()
        if scorer:
            scorer.award_hold_objectives_after_combat(game, results)
        game.update_game_status(finalize=True)
    if scorer:
        scorer.recalculate_scenario_victory(game)
    if not game.finalize_completed_phase():
        game.end_turn()


def apply_live_plan(game, plan, pending, rng, *, score_objectives=False):
    """Apply an already validated order, consume its ID even on interruption.

    Pending is a mutable set of identities, independent of movement points.
    All callers validate their representation before entering this workflow.
    """
    resolution = game.apply_movement_plans([plan])
    pending.discard(plan.unit.id)
    pending.intersection_update(
        u.id for u in game.board.get_units() if u.get_coords() is not None)
    if game.get_game_status().state == "completed" and score_objectives:
        ObjectiveScorer().recalculate_scenario_victory(game)
    if not game.finalize_completed_phase() and not pending:
        finish_side(game, rng, score_objectives=score_objectives)
    return resolution
