"""Shared v2 live-order resolution for training and authoritative games."""

from .live_turn import apply_live_plan, finish_side
from .multi_unit_state import joint_plan

__all__ = ["apply_order", "finish_side"]


def apply_order(game, slots, pending, action, rng):
    """Validate before mutation and observe only after fire resolves."""
    _, plan = joint_plan(game, slots, pending, action)
    combat_start = len(game.combat_log)
    pending_ids = {u.id for u, enabled in zip(slots, pending)
                   if u is not None and enabled}
    resolution = apply_live_plan(game, plan, pending_ids, rng)
    for index, unit in enumerate(slots):
        pending[index] = unit is not None and unit.id in pending_ids
    return (plan, tuple(resolution.defensive_fire_results),
            tuple(game.combat_log[combat_start:]))
