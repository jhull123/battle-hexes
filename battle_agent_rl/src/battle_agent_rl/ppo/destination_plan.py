"""Read-only core route validation shared by policy action contracts."""

from battle_hexes_core.game.movement import MovementCalculator
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan


def destination_plan(board, unit, destination):
    if unit.current_turn_movement_points_remaining != unit.move:
        raise RuntimeError("Pending unit has spent movement points")
    start = board.get_hex(*unit.get_coords())
    path = board.shortest_path(unit, start, destination)
    if not path or path[0] != start or path[-1] != destination:
        raise RuntimeError("Core could not route a legal destination")
    movement = MovementCalculator(board)
    cost = 0
    for origin, target in zip(path, path[1:]):
        if (target not in board.get_neighboring_hexes(origin)
                or not board.can_unit_enter_hex(
                    unit, target.row, target.column)
                or board.enemy_adjacent(unit, origin)):
            raise RuntimeError("Core returned an illegal path")
        cost += movement.move_cost(unit, origin, target)
    if cost > unit.current_turn_movement_points_remaining:
        raise RuntimeError("Core path exceeds movement budget")
    return UnitMovementPlan(unit, path)
