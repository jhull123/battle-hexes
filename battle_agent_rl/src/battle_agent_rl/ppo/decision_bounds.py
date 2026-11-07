"""Derive public-input bounds and enforce the delivered numeric interface."""

from dataclasses import fields
import math

from .decision_contract import ObservationBounds


def terrain_values(tile):
    value = tile.terrain
    return ((1, 1, 0) if value is None else
            (value.move_cost, value.defensive_fire_modifier,
             value.combat_odds_shift))


def _numbers(values, name, low, high, integer=False):
    try:
        invalid = any(not math.isfinite(v) or not low <= v <= high
                      or (integer and int(v) != v) for v in values)
    except (OverflowError, TypeError) as error:
        raise ValueError(f"Unsupported numeric {name}") from error
    if invalid:
        raise ValueError(f"Unsupported {name} for decision input dtype/range")
    return list(values)


def _objective_bounds(game):
    points = _numbers([sum(o.points for o in h.objectives)
                       for h in game.board.hexes],
                      "objective points", 0, 127, True)
    _numbers([o.points for o in game.board.get_objectives()],
             "objective points", 0, 127, True)
    # Supported core objective_control scoring counts objectives, not points.
    score_high = len(game.board.get_objectives())
    _numbers([score_high], "scores", 0, 127, True)
    return max(points), score_high


def validate_dimensions(board_size, turn_limit):
    if turn_limit is None:
        raise ValueError("Decision inputs require a finite positive horizon")
    _numbers([turn_limit, *board_size],
             "horizon/dimensions", 1, 2147483647, True)


def _reinforcement_bound(game):
    groups = game.reinforcements_deployer.groups
    arrivals = [v for g in groups for v in (g.arrival_turn, *g.coords)]
    validate_dimensions((game.board.rows, game.board.columns), game.turn_limit)
    _numbers(arrivals, "reinforcements", 0, 2147483647, True)
    if any(g.arrival_turn < 1 or not game.board.is_in_bounds(*g.coords)
           for g in groups):
        raise ValueError("Unsupported reinforcement arrival or coordinates")
    return max([2, game.board.rows - 1, game.board.columns - 1, *arrivals])


def bounds_for_game(game, slots):
    """Use core-resolved defaults, terrain, roster and all arrival groups."""
    stats = [v for u in slots for v in
             (u.attack, u.defense, u.move, u.defensive_fire_modifier)]
    _numbers(stats, "unit stats", 0, 3.4028234e38)
    movement = _numbers([u.move for u in slots], "movement", 0, 127, True)
    terrain = [v for h in game.board.hexes for v in terrain_values(h)]
    _numbers(terrain, "terrain", -3.4028234e38, 3.4028234e38)
    if any(terrain_values(h)[0] <= 0 or terrain_values(h)[1] < 0
           for h in game.board.hexes):
        raise ValueError("Unsupported terrain movement cost or fire modifier")
    roads = _numbers(list(game.board.get_road_types().values()),
                     "road costs", 0, 3.4028234e38)
    objective_high, score_high = _objective_bounds(game)
    return ObservationBounds(
        max(stats), max(movement), min(0, *terrain), max(0, *terrain),
        max([0, *roads]), objective_high, score_high,
        _reinforcement_bound(game))


def validate_bounds(game, slots, expected):
    actual = bounds_for_game(game, slots)
    for field in fields(expected):
        value = getattr(actual, field.name)
        bound = getattr(expected, field.name)
        outside = (value < bound if field.name.endswith("_low")
                   else value > bound)
        if outside:
            raise ValueError(f"Game exceeds decision bound: {field.name}")
    scores = [game.get_score_tracker().get_score(p) for p in game.players]
    _numbers(scores, "live scores", 0, expected.score_high, True)
