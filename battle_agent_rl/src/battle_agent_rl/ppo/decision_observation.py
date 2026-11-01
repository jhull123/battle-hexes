"""Fresh public-state arrays; encoding never advances, scores or rolls core."""

import numpy as np

from .decision_actions import pending_flags


def observation(binding, pending, active=True):
    game = binding.game
    board = game.board
    result = _unit_arrays(binding)
    result.update(_board_arrays(board))
    result["pending"] = pending_flags(binding, pending, active)
    result["objective_control"] = np.array([
        any(binding.scoring_player.owns(u)
            for u in board.get_units_at(*coords))
        for coords in binding.objective_coords
    ], dtype=np.int8)
    result["scores"] = np.array([
        game.get_score_tracker().get_score(player)
        for player in (binding.learner, binding.opponent)
    ], dtype=np.int8)
    result["reinforcement"] = _reinforcement_array(binding)
    result["remaining_cycles"] = np.array(
        [max(0, binding.spec.turn_limit + 1 - game.turn_number)],
        dtype=np.int32)
    return result


def _unit_arrays(binding):
    units_count = len(binding.slots)
    result = {
        "positions": np.zeros(
            (units_count, binding.spec.cells), dtype=np.int8),
        "unit_status": np.full(units_count, 2, dtype=np.int8),
        "unit_stats": np.array([
            [u.attack, u.defense, u.move, u.defensive_fire_modifier]
            for u in binding.slots
        ], dtype=np.float32),
        "movement_remaining": np.zeros(units_count, dtype=np.int8),
        "fire_flags": np.zeros((units_count, 4), dtype=np.int8),
    }
    units = binding.game.board.get_units()
    awaiting = {u for g in binding.reinforcement_groups if not g.entered
                for u in g.units}
    for index, unit in enumerate(binding.slots):
        if unit not in units or unit.get_coords() is None:
            if unit in awaiting:
                result["unit_status"][index] = 0
            continue
        result["unit_status"][index] = 1
        row, column = unit.get_coords()
        cell = row * binding.spec.board_size[1] + column
        result["positions"][index, cell] = 1
        result["movement_remaining"][index] = (
            unit.current_turn_movement_points_remaining)
        result["fire_flags"][index] = [
            unit.public_defensive_fire_status(binding.learner),
            unit.ended_last_friendly_turn_with_defensive_fire_eligibility,
            unit.forced_to_retreat_since_last_friendly_turn,
            unit.defensive_fire_spent_this_off_turn,
        ]
    return result


def _board_arrays(board):
    cells = board.rows * board.columns
    terrain = np.zeros((cells, 3), dtype=np.float32)
    points = np.zeros(cells, dtype=np.int8)
    for tile in board.hexes:
        cell = tile.row * board.columns + tile.column
        value = tile.terrain
        terrain[cell] = ((1, 1, 0) if value is None else
                         (value.move_cost, value.defensive_fire_modifier,
                          value.combat_odds_shift))
        points[cell] = sum(o.points for o in tile.objectives)
    return {"terrain": terrain, "objective_points": points,
            "road_edges": _road_edges(board)}


def _road_edges(board):
    edges = {}
    costs = board.get_road_types()
    for road_type, path in board.get_road_paths():
        for start, end in zip(path, path[1:]):
            edges[start, end] = edges[end, start] = costs[road_type]
    result = np.zeros((board.rows * board.columns, 6), dtype=np.float32)
    for tile in board.hexes:
        # Match core's column parity, despite the historical R names.
        directions = (board.EVEN_R_DIRECTIONS if tile.column % 2 == 0
                      else board.ODD_R_DIRECTIONS)
        start = (tile.row, tile.column)
        for index, (dr, dc) in enumerate(directions):
            end = (tile.row + dr, tile.column + dc)
            if board.is_in_bounds(*end):
                result[tile.row * board.columns + tile.column, index] = (
                    edges.get((start, end), 0))
    return result


def _reinforcement_array(binding):
    # Core pending() omits entered groups; associate by stable unit identities,
    # not by list position (an earlier group may have already entered).
    statuses = {tuple(u.id for u in g.units): g.status for g in
                binding.game.reinforcements_deployer.pending(
                    binding.game.turn_number)}
    rows = []
    for group in binding.reinforcement_groups:
        status = (2 if group.entered else {"scheduled": 0, "delayed": 1}[
            statuses[tuple(u.id for u in group.units)]])
        rows.append([group.arrival_turn, *group.coords, status])
    return np.array(rows, dtype=np.int32).reshape(-1, 4)
