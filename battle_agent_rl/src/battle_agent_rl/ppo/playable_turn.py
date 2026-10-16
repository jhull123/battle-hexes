"""Shared v2 live-order resolution for training and authoritative games."""

from battle_hexes_core.combat.combat import Combat

from .multi_unit_state import joint_plan


def finish_side(game, rng):
    """Close movement, resolve combat once, then let core advance the turn."""
    game.end_movement()
    if game.current_phase == "combat":
        Combat(game, rng=rng).resolve_combat()
        game.end_combat()
        game.update_game_status(finalize=True)
    if not game.finalize_completed_phase():
        game.end_turn()


def apply_order(game, slots, pending, action, rng):
    """Validate before mutation and observe only after fire resolves."""
    slot, plan = joint_plan(game, slots, pending, action)
    combat_start = len(game.combat_log)
    resolution = game.apply_movement_plans([plan])
    pending[slot] = False
    for index, unit in enumerate(slots):
        if unit is None or unit.get_coords() is None:
            pending[index] = False
    if not game.finalize_completed_phase() and not any(pending):
        finish_side(game, rng)
    return (plan, tuple(resolution.defensive_fire_results),
            tuple(game.combat_log[combat_start:]))
