import random

import pytest

from battle_agent_rl.scripted import ScriptedPlayer
from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.objective import Objective
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.terrain import Terrain
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


def _setup(rows, columns, objectives=(), limit=None):
    board = Board(rows, columns)
    board.set_stacking_limit(limit)
    for coords in objectives:
        board.get_hex(*coords).objectives.append(Objective(coords, 1, "hold"))
    red = Faction("red", "Red", "#C81010")
    blue = Faction("blue", "Blue", "#1010C8")
    scripted = ScriptedPlayer("Scripted", factions=[red], board=board)
    opponent = Player("Opponent", PlayerType.HUMAN, [blue])
    return board, scripted, opponent


def _add(board, player, unit_id, coords, move=1):
    unit = Unit(unit_id, unit_id, player.factions[0], player, "Infantry",
                2, 2, move)
    board.add_unit(unit, *coords)
    return unit


def _coords(hex_):
    return hex_.row, hex_.column


def _destinations(plans):
    return [(plan.unit.get_id(), _coords(plan.path[-1])) for plan in plans]


def _next_scripted_turn(game):
    game.next_player()
    game.next_player()


def test_no_objectives_means_no_orders_even_if_a_unit_can_move():
    board, player, _ = _setup(2, 2)
    unit = _add(board, player, "red", (0, 0), move=2)
    assert player.type is PlayerType.CPU
    assert board.get_hex(0, 1) in board.get_reachable_hexes(
        unit, board.get_hex(0, 0)
    )

    assert player.movement() == []
    player.movement_cb()
    player.combat_results(CombatResults())
    player.end_game_cb()

    assert board.get_units() == [unit]
    assert unit.get_coords() == (0, 0)
    assert unit.current_turn_movement_points_remaining == 2


def test_units_choose_independent_targets_without_mutating_the_game():
    board, player, enemy = _setup(6, 3, [(0, 0), (5, 0)])
    a = _add(board, player, "a", (1, 0))
    b = _add(board, player, "b", (2, 0), move=2)
    c = _add(board, player, "c", (4, 0))
    _add(board, enemy, "enemy", (0, 2), move=2)
    removed = _add(board, player, "removed", (3, 0))
    board.remove_units([removed])
    before = [
        (unit, unit.get_coords(), unit.current_turn_movement_points_remaining)
        for unit in board.get_units()
    ]
    rng_state = random.getstate()

    for _ in range(2):
        plans = player.movement()
        assert [plan.unit for plan in plans] == [a, b, c]
        assert [list(map(_coords, plan.path)) for plan in plans] == [
            [(1, 0), (0, 0)], [(2, 0), (1, 0), (0, 0)], [(4, 0), (5, 0)],
        ]
    assert [
        (unit, unit.get_coords(), unit.current_turn_movement_points_remaining)
        for unit in board.get_units()
    ] == before
    assert random.getstate() == rng_state


@pytest.mark.parametrize(("start", "first", "second"), [
    ((2, 0), (1, 0), (3, 0)),
    ((2, 1), (2, 0), (2, 2)),
])
def test_equal_distance_targets_use_coordinates_not_points(
    start, first, second, monkeypatch,
):
    board, player, _ = _setup(4, 3)
    board.get_hex(*first).objectives.append(Objective(first, 1, "hold"))
    board.get_hex(*second).objectives.append(Objective(second, 5, "occupy"))
    _add(board, player, "a", start)

    assert _destinations(player.movement()) == [("a", first)]
    objectives = board.get_objectives()
    monkeypatch.setattr(board, "get_objectives", lambda: objectives[::-1])
    assert _destinations(player.movement()) == [("a", first)]


def test_unit_advances_over_multiple_turns_and_then_holds():
    board, player, enemy = _setup(8, 1, [(7, 0)])
    mover = _add(board, player, "a", (2, 0), move=2)
    _add(board, enemy, "enemy", (0, 0))
    game = Game([player, enemy], board)

    for expected in [(4, 0), (6, 0), (7, 0)]:
        game.apply_movement_plans(player.movement())
        assert mover.get_coords() == expected
        _next_scripted_turn(game)

    assert player.movement() == []


def test_terrain_and_remaining_budget_limit_progress():
    board, player, _ = _setup(5, 1, [(4, 0)])
    mover = _add(board, player, "a", (0, 0), move=4)
    mover.current_turn_movement_points_remaining = 2
    board.get_hex(1, 0).set_terrain(Terrain("Rough", "#888888", move_cost=2))

    assert _destinations(player.movement()) == [("a", (1, 0))]


def test_enemy_objective_is_approached_instead_of_switching_targets():
    board, player, enemy = _setup(6, 1, [(5, 0), (0, 0)])
    mover = _add(board, player, "a", (3, 0), move=3)
    _add(board, enemy, "enemy", (5, 0))
    game = Game([player, enemy], board)

    assert _destinations(player.movement()) == [("a", (4, 0))]
    game.apply_movement_plans(player.movement())
    _next_scripted_turn(game)
    assert mover.get_coords() == (4, 0)
    assert player.movement() == []


def test_unit_waits_next_to_a_full_objective_then_enters_when_space_opens():
    target = (2, 2)
    board, player, enemy = _setup(5, 5, [target, (4, 4)], limit=2)
    mover = _add(board, player, "a", (2, 0))
    occupant = _add(board, player, "occupant", target)
    _add(board, player, "other occupant", target)
    _add(board, enemy, "enemy", (0, 4))
    game = Game([player, enemy], board)

    assert _destinations(player.movement()) == [("a", (1, 1))]
    game.apply_movement_plans(player.movement())
    _next_scripted_turn(game)
    assert mover.get_coords() == (1, 1)
    assert player.movement() == []

    board.remove_units([occupant])
    _next_scripted_turn(game)
    assert _destinations(player.movement()) == [("a", target)]
    game.apply_movement_plans(player.movement())
    assert mover.get_coords() == target
    assert len(board.get_units_at(*target)) == 2


@pytest.mark.parametrize("ids", [("a", "b"), ("b", "a")])
def test_units_contend_for_the_last_slot_next_to_a_full_objective(ids):
    board, player, _ = _setup(5, 1, [(4, 0)], limit=2)
    for unit_id in ids:
        _add(board, player, unit_id, (1, 0), move=2)
    _add(board, player, "c", (3, 0))
    _add(board, player, "d", (4, 0))
    _add(board, player, "e", (4, 0))

    assert _destinations(player.movement()) == [("a", (3, 0)), ("b", (2, 0))]


def test_first_unit_claims_the_last_slot_on_the_objective():
    board, player, _ = _setup(4, 1, [(1, 0)], limit=1)
    _add(board, player, "b", (2, 0))
    _add(board, player, "a", (0, 0))

    assert _destinations(player.movement()) == [("a", (1, 0))]


def test_later_plan_uses_vacated_hex_but_cannot_pass_through_new_stack():
    board, player, enemy = _setup(8, 1, [(5, 0)], limit=1)
    a = _add(board, player, "a", (2, 0))
    b = _add(board, player, "b", (1, 0), move=4)
    _add(board, enemy, "enemy", (7, 0))
    game = Game([player, enemy], board)

    plans = player.movement()
    assert _destinations(plans) == [("a", (3, 0)), ("b", (2, 0))]
    game.apply_movement_plans(plans)
    assert (a.get_coords(), b.get_coords()) == ((3, 0), (2, 0))


def test_later_unit_can_take_an_alternate_route_around_reserved_hex():
    board, player, _ = _setup(5, 3, [(4, 1)], limit=1)
    _add(board, player, "a", (2, 1))
    _add(board, player, "b", (2, 0), move=3)

    plans = player.movement()
    assert _destinations(plans) == [("a", (3, 1)), ("b", (4, 1))]
    assert (3, 1) not in list(map(_coords, plans[1].path))


def test_each_turn_selects_nearest_objective_from_actual_position():
    board, player, _ = _setup(9, 1, [(0, 0), (8, 0)])
    mover = _add(board, player, "a", (3, 0))
    assert _destinations(player.movement()) == [("a", (2, 0))]

    mover.set_coords(5, 0)
    assert _destinations(player.movement()) == [("a", (6, 0))]


def test_defensive_fire_can_invalidate_a_later_planned_move():
    board, player, enemy = _setup(5, 1, [(4, 0)], limit=1)
    a = _add(board, player, "a", (2, 0))
    b = _add(board, player, "b", (1, 0), move=3)
    _add(board, enemy, "enemy", (4, 0))
    game = Game([player, enemy], board)
    game.set_defensive_fire_settings(
        DefensiveFireSettings(base_probability=1.0),
    )

    plans = player.movement()
    assert _destinations(plans) == [("a", (3, 0)), ("b", (2, 0))]
    result = game.apply_movement_plans(plans)
    assert result.defensive_fire_results[0].retreat_destination == (2, 0)
    assert (a.get_coords(), b.get_coords()) == ((2, 0), (1, 0))
