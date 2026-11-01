"""Exact public inputs audited against real core state and transitions."""

import numpy as np

from battle_hexes_core.game.movement import MovementCalculator
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from battle_agent_rl.ppo.decision_actions import (
    action_mask, pending_at_movement_start,
)
from battle_agent_rl.ppo.crossroads_contract import observation_space
from battle_agent_rl.ppo.decision_observation import observation
from battle_agent_rl.ppo.crossroads_scenario import bind_game


def test_concrete_spaces_and_dtypes_remain_the_08_contract(german_decision):
    from gymnasium import spaces

    expected = spaces.Dict({
        "positions": spaces.MultiBinary((11, 324)),
        "unit_status": spaces.Box(0, 2, (11,), dtype=np.int8),
        "unit_stats": spaces.Box(0, 7, (11, 4), dtype=np.float32),
        "movement_remaining": spaces.Box(0, 7, (11,), dtype=np.int8),
        "fire_flags": spaces.MultiBinary((11, 4)),
        "pending": spaces.MultiBinary(5),
        "terrain": spaces.Box(-2, 3, (324, 3), dtype=np.float32),
        "road_edges": spaces.Box(0, 1, (324, 6), dtype=np.float32),
        "objective_points": spaces.Box(0, 1, (324,), dtype=np.int8),
        "objective_control": spaces.MultiBinary(3),
        "scores": spaces.Box(0, 3, (2,), dtype=np.int8),
        "reinforcement": spaces.Box(0, 17, (1, 4), dtype=np.int32),
        "remaining_cycles": spaces.Box(0, 8, (1,), dtype=np.int32),
    })
    assert observation_space() == expected
    obs = observation(german_decision, set())
    assert obs.keys() == expected.spaces.keys()
    for key, value in obs.items():
        assert value.dtype == expected[key].dtype
        assert value.shape == expected[key].shape


def test_opening_hold_observation_exact_values(german_decision):
    b = german_decision
    pending = pending_at_movement_start(b)
    obs = observation(b, pending)
    assert observation_space().contains(obs)
    assert obs["positions"].shape == (11, 324)
    assert obs["positions"].argmax(axis=1).tolist() == [
        69, 77, 117, 0, 0, 227, 223, 286, 289, 288, 295]
    assert obs["positions"].sum(axis=1).tolist() == [1, 1, 1, 0, 0] + [1] * 6
    assert obs["unit_status"].tolist() == [1, 1, 1, 0, 0] + [1] * 6
    np.testing.assert_allclose(obs["unit_stats"], [
        [2, 2, 4, 1], [2, 2, 4, 1], [1, 1, 0, .5],
        [1, 2, 3, 1.33], [4, 4, 7, 1.33], *([[3, 2, 5, 1]] * 6)])
    assert obs["movement_remaining"].tolist() == [4, 4, 0, 0, 0] + [5] * 6
    assert obs["fire_flags"].tolist() == (
        [[1, 1, 0, 0]] * 3 + [[0, 0, 0, 0]] * 2 + [[1, 1, 0, 0]] * 6)
    assert obs["pending"].tolist() == [1, 1, 1, 0, 0]
    assert obs["scores"].tolist() == [3, 0]
    assert obs["objective_control"].tolist() == [0, 0, 0]
    assert np.flatnonzero(obs["objective_points"]).tolist() == [39, 69, 117]
    assert obs["reinforcement"].tolist() == [[3, 0, 16, 0]]
    assert obs["remaining_cycles"].tolist() == [8]
    np.testing.assert_allclose(obs["terrain"][[0, 1, 8, 39]], [
        [2, .85, -1], [1, 1, 0], [3, .75, -2], [1, .75, -1]])


def test_fresh_arrays_and_insertion_independence(german_decision):
    b = german_decision
    pending = pending_at_movement_start(b)
    original = observation(b, pending)
    b.game.board.units = dict(reversed(list(b.game.board.units.items())))
    rebound = bind_game(b.game, b.learner)
    again = observation(rebound, pending)
    for key in original:
        assert not np.shares_memory(original[key], again[key])
        np.testing.assert_array_equal(original[key], again[key])
        again[key].fill(0)
        np.testing.assert_array_equal(
            original[key], observation(b, pending)[key])


def test_stacks_elimination_readiness_and_uncomputed_scores(german_decision):
    b = german_decision
    board = b.game.board
    pending = pending_at_movement_start(b)
    b.slots[1].set_coords(*b.slots[0].get_coords())
    b.slots[0].record_forced_retreat(b.learner)
    b.slots[5].spend_defensive_fire(b.learner)
    board.remove_units(b.slots[2])
    b.slots[6].set_coords(2, 3)
    obs = observation(b, pending)
    assert obs["positions"][0, 69] == obs["positions"][1, 69] == 1
    assert obs["fire_flags"][0].tolist() == [0, 1, 1, 0]
    assert obs["fire_flags"][5].tolist() == [0, 1, 0, 1]
    assert obs["unit_status"][2] == 2
    assert not obs["positions"][2].any()
    assert not obs["fire_flags"][2].any()
    assert obs["movement_remaining"][2] == 0
    assert obs["unit_stats"][2].tolist() == [1, 1, 0, .5]
    assert obs["pending"].tolist() == [1, 1, 0, 0, 0]
    assert obs["objective_control"].tolist() == [1, 0, 0]
    assert obs["scores"].tolist() == [3, 0]  # Encoding does not score.
    ObjectiveScorer().recalculate_scenario_victory(b.game)
    assert observation(b, pending)["scores"].tolist() == [2, 1]


def test_roads_follow_core_offsets_without_affecting_cost(german_decision):
    b = german_decision
    board = b.game.board
    obs = observation(b, pending_at_movement_start(b))
    edges = {}
    for name, path in board.get_road_paths():
        for a, z in zip(path, path[1:]):
            edges[a, z] = edges[z, a] = board.get_road_types()[name]
    for row in range(18):
        for col in range(18):
            directions = (board.EVEN_R_DIRECTIONS if col % 2 == 0 else
                          board.ODD_R_DIRECTIONS)
            for direction, (dr, dc) in enumerate(directions):
                target = (row + dr, col + dc)
                expected = (edges.get(((row, col), target), 0)
                            if board.is_in_bounds(*target) else 0)
                assert obs["road_edges"][row * 18 + col, direction] == expected
    # Declared road into the rough cell (5,9) still costs two movement points.
    start, end = board.get_hex(6, 9), board.get_hex(5, 9)
    board.set_road_paths([("secondary", ((6, 9), (5, 9)))])
    assert observation(b, set())["road_edges"][117, 0] == 1
    assert MovementCalculator(board).move_cost(b.slots[0], start, end) == 2


def test_true_horizon_and_disabled_pending(german_decision):
    b = german_decision
    pending = pending_at_movement_start(b)
    b.game.turn_number = 3
    obs = observation(b, pending, active=False)
    assert obs["remaining_cycles"].tolist() == [6]
    assert not obs["pending"].any()
    assert not action_mask(b, pending, active=False).any()
    assert observation_space().contains(obs)
    b.game.turn_number = 9
    assert observation(b, set())["remaining_cycles"].tolist() == [0]


def test_off_board_coordinates_do_not_override_core_lifecycle(german_decision):
    b = german_decision
    b.game.board.remove_units(b.slots[0])
    b.slots[0].set_coords(3, 15)  # Stale coordinates are not board membership.
    b.slots[3].set_coords(0, 16)  # Nor do they deploy a reserved unit.
    obs = observation(b, set())
    assert obs["unit_status"][:5].tolist() == [2, 1, 1, 0, 0]
    assert not obs["positions"][[0, 3]].any()
    assert not obs["movement_remaining"][[0, 3]].any()
    assert not obs["fire_flags"][[0, 3]].any()
