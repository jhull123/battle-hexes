"""Read-only pending-unit masks and validated single-order conversion."""

from numbers import Integral

import numpy as np

from .crossroads_contract import ACTIONS, CELLS, COLUMNS, LEARNER_IDS
from .destination_plan import destination_plan


def _movement_active(binding, active):
    game = binding.game
    return (active and game.get_game_status().state == "in_progress"
            and game.get_current_player() is binding.learner
            and game.current_phase == "movement")


def pending_at_movement_start(binding):
    """Snapshot IDs once per friendly movement start, including Feldwache.

    The future turn driver owns consumption; do not rebuild pending
    after an order (a hold can leave movement points unchanged).
    """
    if not _movement_active(binding, True):
        raise RuntimeError("Pending orders require Wehrmacht movement")
    board_units = binding.game.board.get_units()
    return frozenset(unit.id for unit in binding.slots[:5]
                     if unit in board_units and unit.get_coords() is not None)


def pending_flags(binding, pending, active=True):
    if not set(pending).issubset(LEARNER_IDS):
        raise ValueError("Unknown Wehrmacht pending identity")
    board_units = binding.game.board.get_units()
    enabled = _movement_active(binding, active)
    return np.array([
        enabled and unit.id in pending and unit in board_units
        and unit.get_coords() is not None for unit in binding.slots[:5]
    ], dtype=np.int8)


def action_mask(binding, pending, active=True):
    """Fresh core reachability mask; no orders or RNG are consumed."""
    mask = np.zeros(ACTIONS, dtype=np.bool_)
    board = binding.game.board
    for slot, enabled in enumerate(pending_flags(binding, pending, active)):
        if not enabled:
            continue
        unit = binding.slots[slot]
        if unit.current_turn_movement_points_remaining != unit.move:
            raise RuntimeError("Pending unit has spent movement points")
        start = board.get_hex(*unit.get_coords())
        for tile in board.get_reachable_hexes(unit, start, unit.move):
            mask[slot * CELLS + tile.row * COLUMNS + tile.column] = True
    return mask


def action_plan(binding, pending, action, active=True):
    """Return (permanent slot, core plan), leaving execution to the caller."""
    if isinstance(action, np.ndarray) and action.shape == ():
        action = action.item()
    if (isinstance(action, bool) or not isinstance(action, Integral)
            or not 0 <= action < ACTIONS):
        raise ValueError("Action must be a scalar integer in [0, 1620)")
    if not action_mask(binding, pending, active)[action]:
        raise ValueError("Action is not a legal pending Wehrmacht destination")
    slot, cell = divmod(int(action), CELLS)
    destination = binding.game.board.get_hex(*divmod(cell, COLUMNS))
    return slot, destination_plan(
        binding.game.board, binding.slots[slot], destination)
