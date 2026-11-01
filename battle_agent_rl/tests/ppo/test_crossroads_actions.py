"""Core reachability, pending identity and invalid-action non-mutation."""

from copy import deepcopy

import numpy as np
import pytest

from battle_agent_rl.ppo.decision_actions import (
    action_mask, action_plan, pending_at_movement_start,
)
from battle_agent_rl.ppo.crossroads_contract import action_space
from battle_agent_rl.ppo.decision_observation import observation


def snapshot(binding, pending):
    game = binding.game
    units = [
        {k: v for k, v in vars(u).items() if k not in ("_player", "faction")}
        for u in binding.slots]
    return deepcopy((units, tuple(u.id for u in game.board.get_units()),
                     tuple(u.id for u in game.board.get_known_units()),
                     game.turn_number, game.current_phase,
                     game.get_current_player().name, game.get_game_status(),
                     game.pending_combats, game.defensive_fire_log,
                     game.combat_log, game.reinforcements_deployer.game_log,
                     tuple((g.id, g.arrival_turn, g.coords, g.entered,
                            tuple(u.id for u in g.units))
                           for g in binding.reinforcement_groups),
                     game.score_tracker.get_scores(), set(pending),
                     game.defensive_fire_resolver.rng.getstate()))


def test_mask_exactly_matches_core_and_all_destinations_route(german_decision):
    b = german_decision
    pending = pending_at_movement_start(b)
    mask = action_mask(b, pending)
    assert mask.shape == (1620,) and mask.dtype == np.bool_
    assert np.flatnonzero(mask[648:972]).tolist() == [117]
    assert not mask[972:].any()
    assert mask[69] and mask[401] and mask[765]
    for slot, unit in enumerate(b.slots[:3]):
        board = b.game.board
        reachable = board.get_reachable_hexes(
            unit, board.get_hex(*unit.get_coords()), unit.move)
        assert set(np.flatnonzero(mask[slot * 324:(slot + 1) * 324])) == {
            tile.row * 18 + tile.column for tile in reachable}
    before = snapshot(b, pending)
    for action in np.flatnonzero(mask):
        slot, plan = action_plan(b, pending, action)
        assert action_space().contains(action)
        assert plan.unit is b.slots[slot]
        assert (plan.path[0].row, plan.path[0].column) == (
            plan.unit.get_coords())
        assert (plan.path[-1].row, plan.path[-1].column) == divmod(
            int(action) % 324, 18)
    # Conversion is not execution or pending-order consumption.
    assert snapshot(b, pending) == before
    mask.fill(False)
    assert action_mask(b, pending).any()


@pytest.mark.parametrize("action", [
    True, False, np.bool_(True), -1, 1620, 10**30, 69.0, "69", None,
    np.array([69]), np.array([[69]]), np.array(69.0), np.array(True),
    0, 988, 1312, 766,
])
def test_invalid_actions_preserve_state(german_decision, action):
    b = german_decision
    pending = set(pending_at_movement_start(b))
    before = snapshot(b, pending)
    with pytest.raises(ValueError):
        action_plan(b, pending, action)
    assert snapshot(b, pending) == before


@pytest.mark.parametrize("action", [
    69, np.int32(69), np.int64(69), np.array(69)])
def test_scalar_integer_holds(german_decision, action):
    b = german_decision
    _, plan = action_plan(b, pending_at_movement_start(b), action)
    assert len(plan.path) == 1


@pytest.mark.parametrize("bad_path", [
    "empty", "start", "end", "jump", "budget"])
def test_invalid_core_routes_are_non_mutating(
        german_decision, monkeypatch, bad_path):
    b = german_decision
    pending = set(pending_at_movement_start(b))
    board = b.game.board
    start = board.get_hex(3, 15)
    neighbor = board.get_neighboring_hexes(start)[0]
    if bad_path == "empty":
        path = []
    elif bad_path == "start":
        path = [neighbor, start]
    elif bad_path == "end":
        path = [start, neighbor]
    elif bad_path == "jump":
        path = [start, board.get_hex(17, 17), start]
    else:
        path = [start, neighbor, start, neighbor, start, neighbor, start]
    before = snapshot(b, pending)
    monkeypatch.setattr(board, "shortest_path", lambda *args: path)
    with pytest.raises(RuntimeError):
        action_plan(b, pending, 69)
    assert snapshot(b, pending) == before


def test_partial_allowance_is_rejected_without_mutation(german_decision):
    b = german_decision
    pending = pending_at_movement_start(b)
    b.slots[0].current_turn_movement_points_remaining -= 1
    before = snapshot(b, pending)
    with pytest.raises(RuntimeError):
        action_plan(b, pending, 69)
    assert snapshot(b, pending) == before


@pytest.mark.parametrize("state", ["spent", "eliminated", "awaiting"])
def test_unavailable_unit_action_is_non_mutating(german_decision, state):
    b = german_decision
    pending = set(pending_at_movement_start(b))
    action = 69
    if state == "spent":
        pending.remove(b.slots[0].id)
    elif state == "eliminated":
        b.game.board.remove_units(b.slots[0])
    else:
        # Even a stale/fabricated pending ID cannot activate a reserved slot.
        pending.add(b.slots[3].id)
        action = 988
    before = snapshot(b, pending)
    with pytest.raises(ValueError):
        action_plan(b, pending, action)
    assert snapshot(b, pending) == before


def test_pending_masks_hold_casualty_and_reversed_unit_order(german_decision):
    b = german_decision
    pending = set(pending_at_movement_start(b))
    slot, plan = action_plan(b, pending, 401)  # B may act before A.
    b.game.apply_movement_plans([plan])
    pending.remove(b.slots[slot].id)  # Future turn driver owns consumption.
    assert b.slots[1].current_turn_movement_points_remaining == 4
    assert not action_mask(b, pending)[324:648].any()
    before = snapshot(b, pending)
    with pytest.raises(ValueError):
        action_plan(b, pending, 401)
    assert snapshot(b, pending) == before
    b.game.board.remove_units(b.slots[0])  # A stale pending ID cannot act.
    assert observation(b, pending)["pending"].tolist() == [0, 0, 1, 0, 0]
    assert np.flatnonzero(action_mask(b, pending)).tolist() == [765]
    pending.remove(b.slots[2].id)
    assert not action_mask(b, pending).any()


def test_wrong_phase_side_and_completion_never_offer_actions(german_decision):
    b = german_decision
    pending = pending_at_movement_start(b)
    b.game.current_phase = "end_turn"
    assert not action_mask(b, pending).any()
    with pytest.raises(ValueError):
        action_plan(b, pending, 69)
    with pytest.raises(RuntimeError):
        pending_at_movement_start(b)
    b.game.end_turn()
    assert b.game.get_current_player() is b.opponent
    assert not action_mask(b, pending).any()
    b.game.turn_number = 8
    b.game.next_player()
    b.game.end_turn()  # Core turn-limit completion.
    assert b.game.get_game_status().state == "completed"
    assert not action_mask(b, pending).any()
    assert not observation(b, pending)["pending"].any()


@pytest.mark.parametrize("roll", [0.0, 0.99])
def test_inputs_after_real_core_defensive_fire(german_decision, roll):
    b = german_decision
    b.slots[0].set_coords(3, 4)
    b.slots[1].set_coords(4, 4)
    b.slots[5].set_coords(4, 6)
    pending = set(pending_at_movement_start(b))
    b.game.defensive_fire_resolver.rng.random = lambda: roll
    slot, plan = action_plan(b, pending, 59)  # (3,5): enters enemy adjacency.
    resolution = b.game.apply_movement_plans([plan])
    pending.remove(b.slots[slot].id)
    assert len(resolution.defensive_fire_results) == 1
    obs = observation(b, pending)
    assert obs["fire_flags"][5].tolist() == [0, 1, 0, 1]
    assert obs["movement_remaining"][0] == 0
    assert obs["fire_flags"][0, 2] == (roll == 0)
    assert obs["positions"][0].argmax() == (58 if roll == 0 else 59)
    assert obs["pending"].tolist() == [0, 1, 1, 0, 0]
    assert not action_mask(b, pending)[:324].any()
