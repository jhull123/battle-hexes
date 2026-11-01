"""Read-only pending-unit masks and validated single-order conversion."""

from numbers import Integral

import numpy as np

from .destination_plan import destination_plan


def _movement_active(binding, active):
    game = binding.game
    return (active and game.get_game_status().state == "in_progress"
            and game.get_current_player() is binding.learner
            and game.current_phase == "movement")


def pending_at_movement_start(binding):
    """Snapshot IDs at friendly movement start, including immobile units.

    The future turn driver owns consumption; do not rebuild pending
    after an order (a hold can leave movement points unchanged).
    """
    if not _movement_active(binding, True):
        raise RuntimeError("Pending orders require learner movement")
    board_units = binding.game.board.get_units()
    return frozenset(unit.id for unit in binding.learner_slots
                     if unit in board_units and unit.get_coords() is not None)


def pending_flags(binding, pending, active=True):
    if not set(pending).issubset(binding.spec.learner_ids):
        raise ValueError("Unknown learner pending identity")
    board_units = binding.game.board.get_units()
    enabled = _movement_active(binding, active)
    return np.array([
        enabled and unit.id in pending and unit in board_units
        and unit.get_coords() is not None for unit in binding.learner_slots
    ], dtype=np.int8)


def action_mask(binding, pending, active=True):
    """Fresh core reachability mask; no orders or RNG are consumed."""
    spec = binding.spec
    mask = np.zeros(spec.actions, dtype=np.bool_)
    board = binding.game.board
    for slot, enabled in enumerate(pending_flags(binding, pending, active)):
        if not enabled:
            continue
        unit = binding.slots[slot]
        if unit.current_turn_movement_points_remaining != unit.move:
            raise RuntimeError("Pending unit has spent movement points")
        start = board.get_hex(*unit.get_coords())
        for tile in board.get_reachable_hexes(unit, start, unit.move):
            mask[slot * spec.cells + tile.row * spec.board_size[1]
                 + tile.column] = True
    return mask


def action_plan(binding, pending, action, active=True):
    """Return (permanent slot, core plan), leaving execution to the caller."""
    if isinstance(action, np.ndarray) and action.shape == ():
        action = action.item()
    spec = binding.spec
    if (isinstance(action, bool) or not isinstance(action, Integral)
            or not 0 <= action < spec.actions):
        raise ValueError(
            f"Action must be a scalar integer in [0, {spec.actions})")
    if not action_mask(binding, pending, active)[action]:
        raise ValueError("Action is not a legal pending learner destination")
    slot, cell = divmod(int(action), spec.cells)
    destination = binding.game.board.get_hex(*divmod(cell, spec.board_size[1]))
    return slot, destination_plan(
        binding.game.board, binding.slots[slot], destination)
