"""Stable slot-indexed policy inputs, legal joint actions, and core plans."""

from numbers import Integral

from .destination_plan import destination_plan


CELLS = 81
ACTIONS = 2 * CELLS
CONTRACT = "battle-hexes-9x9-2slot-unit-destination-live-v1"


def joint_mask(game, slots, pending, active=True):
    mask = [False] * ACTIONS
    if not active or game.get_game_status().state != "in_progress":
        return tuple(mask)
    board = game.get_board()
    for slot, unit in enumerate(slots):
        if not pending[slot] or unit is None or unit.get_coords() is None:
            continue
        start = board.get_hex(*unit.get_coords())
        reachable = board.get_reachable_hexes(
            unit, start, unit.current_turn_movement_points_remaining)
        for tile in reachable:
            mask[slot * CELLS + tile.row * 9 + tile.column] = True
    return tuple(mask)


def joint_plan(game, slots, pending, action):
    """Validate everything before returning a plan; never mutate on failure."""
    mask = joint_mask(game, slots, pending)
    if isinstance(action, bool) or not isinstance(action, Integral) \
            or not 0 <= action < ACTIONS or not mask[action]:
        raise ValueError("Action is not a legal joint destination")
    slot, cell = divmod(int(action), CELLS)
    unit = slots[slot]
    board = game.get_board()
    destination = board.get_hex(*divmod(cell, 9))
    return slot, destination_plan(board, unit, destination)


def slot_observation(game, slots, pending, remaining_cycles, learner):
    board = game.get_board()
    result = {key: [0] * 4 for key in (
        "present", "alive", "movement_remaining", "defensive_fire_ready",
        "fire_eligible_last_turn", "forced_retreat", "fire_spent")}
    result["positions"] = [[0] * CELLS for _ in range(4)]
    for index, unit in enumerate(slots):
        if unit is None:
            continue
        result["present"][index] = 1
        if unit not in board.get_units() or unit.get_coords() is None:
            continue
        result["alive"][index] = 1
        row, column = unit.get_coords()
        result["positions"][index][row * 9 + column] = 1
        result["movement_remaining"][index] = (
            unit.current_turn_movement_points_remaining)
        result["defensive_fire_ready"][index] = int(
            unit.public_defensive_fire_status(learner))
        result["fire_eligible_last_turn"][index] = int(
            unit.ended_last_friendly_turn_with_defensive_fire_eligibility)
        result["forced_retreat"][index] = int(
            unit.forced_to_retreat_since_last_friendly_turn)
        result["fire_spent"][index] = int(
            unit.defensive_fire_spent_this_off_turn)
    result["pending"] = list(pending)
    result["remaining_cycles"] = [remaining_cycles]
    return result
