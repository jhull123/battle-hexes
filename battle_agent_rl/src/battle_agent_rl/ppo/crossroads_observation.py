"""Fresh public-state arrays; encoding never advances, scores or rolls core."""

import numpy as np

from .crossroads_actions import pending_flags
from .crossroads_contract import CELLS, COLUMNS


def observation(binding, pending, active=True):
    game = binding.game
    board = game.board
    group = binding.reinforcement_group
    result = _unit_arrays(binding)
    result.update(_board_arrays(board))
    result["pending"] = pending_flags(binding, pending, active)
    result["objective_control"] = np.array([
        any(binding.opponent.owns(u) for u in board.get_units_at(*coords))
        for coords in binding.objective_coords
    ], dtype=np.int8)
    result["scores"] = np.array([
        game.get_score_tracker().get_score(player)
        for player in (binding.learner, binding.opponent)
    ], dtype=np.int8)
    status = (2 if group.entered else
              {"scheduled": 0, "delayed": 1}[
                  game.reinforcements_deployer.pending(game.turn_number)[0]
                  .status])
    result["reinforcement"] = np.array([
        [group.arrival_turn, *group.coords, status]
    ], dtype=np.int32)
    result["remaining_cycles"] = np.array(
        [max(0, 9 - game.turn_number)], dtype=np.int32)
    return result


def _unit_arrays(binding):
    result = {
        "positions": np.zeros((11, CELLS), dtype=np.int8),
        "unit_status": np.full(11, 2, dtype=np.int8),
        "unit_stats": np.array([
            [u.attack, u.defense, u.move, u.defensive_fire_modifier]
            for u in binding.slots
        ], dtype=np.float32),
        "movement_remaining": np.zeros(11, dtype=np.int8),
        "fire_flags": np.zeros((11, 4), dtype=np.int8),
    }
    units = binding.game.board.get_units()
    group = binding.reinforcement_group
    for index, unit in enumerate(binding.slots):
        if unit not in units or unit.get_coords() is None:
            if unit in group.units and not group.entered:
                result["unit_status"][index] = 0
            continue
        result["unit_status"][index] = 1
        row, column = unit.get_coords()
        result["positions"][index, row * COLUMNS + column] = 1
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
    terrain = np.zeros((CELLS, 3), dtype=np.float32)
    points = np.zeros(CELLS, dtype=np.int8)
    for tile in board.hexes:
        cell = tile.row * COLUMNS + tile.column
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
    result = np.zeros((CELLS, 6), dtype=np.float32)
    for tile in board.hexes:
        # Match core's column parity, despite the historical R names.
        directions = (board.EVEN_R_DIRECTIONS if tile.column % 2 == 0
                      else board.ODD_R_DIRECTIONS)
        start = (tile.row, tile.column)
        for index, (dr, dc) in enumerate(directions):
            end = (tile.row + dr, tile.column + dc)
            if board.is_in_bounds(*end):
                result[tile.row * COLUMNS + tile.column, index] = (
                    edges.get((start, end), 0))
    return result
