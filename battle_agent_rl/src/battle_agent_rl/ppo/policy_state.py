"""Core-state policy inputs and destination plans for the fixed 1v1 task."""

from battle_hexes_core.game.unitmovementplan import UnitMovementPlan


ROWS = COLUMNS = 5


def observation(game, learner, remaining_steps):
    board = game.get_board()
    occupants = [board.get_unit_at(tile.row, tile.column)
                 for tile in board.hexes]
    return {
        "occupancy": tuple(
            0 if unit is None else 1 if learner.owns(unit) else -1
            for unit in occupants
        ),
        "defensive_fire_ready": tuple(
            int(unit.public_defensive_fire_status(learner))
            if unit is not None else 0 for unit in occupants
        ),
        "remaining_steps": remaining_steps,
    }


def action_mask(game, learner, active=True):
    board = game.get_board()
    units = board.get_units_for_player(learner)
    if not active or game.get_game_status().state != "in_progress" \
            or not units:
        return (False,) * (ROWS * COLUMNS)
    unit = units[0]
    start = board.get_hex(*unit.get_coords())
    reachable = board.get_reachable_hexes(unit, start)
    return tuple(tile in reachable for tile in board.hexes)


def action_plan(game, learner, action):
    """Route the selected destination from the unit's *current* position."""
    board = game.get_board()
    unit = board.get_units_for_player(learner)[0]
    destination = board.get_hex(*divmod(action, COLUMNS))
    start = board.get_hex(*unit.get_coords())
    path = board.shortest_path(unit, start, destination)
    if not path or path[0] != start or path[-1] != destination:
        raise RuntimeError("Core could not route a legal destination")
    return UnitMovementPlan(unit, path)
