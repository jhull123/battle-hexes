"""Reserved slots across core arrival, blocked retry and casualty lifecycle."""

import numpy as np

from battle_hexes_core.game.unitmovementplan import UnitMovementPlan

from battle_agent_rl.ppo.crossroads_actions import (
    action_mask, action_plan, pending_at_movement_start,
)
from battle_agent_rl.ppo.crossroads_contract import observation_space
from battle_agent_rl.ppo.crossroads_observation import observation
from battle_agent_rl.ppo.crossroads_scenario import bind_game


def test_arrival_before_airborne_then_casualty_before_first_order(
        crossroads, close_unopposed_side):
    b = crossroads
    for _ in range(4):
        close_unopposed_side(b.game)
    assert b.game.turn_number == 3
    assert b.game.get_current_player() is b.opponent
    assert b.slots[3].get_coords() == b.slots[4].get_coords() == (0, 16)
    assert not b.slots[3].has_defensive_fire(b.opponent)
    assert not b.slots[4].has_defensive_fire(b.opponent)
    obs = observation(b, set())
    assert obs["unit_status"][3:5].tolist() == [1, 1]
    assert obs["positions"][3, 16] == obs["positions"][4, 16] == 1
    assert obs["reinforcement"].tolist() == [[3, 0, 16, 2]]
    assert not action_mask(b, set()).any()  # Still Airborne's turn.
    b.slots[5].set_coords(2, 16)
    board = b.game.board
    result = b.game.apply_movement_plans([UnitMovementPlan(
        b.slots[5], [board.get_hex(2, 16), board.get_hex(1, 16)])])
    assert not result.defensive_fire_results  # Arrivals cannot shoot yet.
    b.slots[5].set_coords(12, 11)
    board.remove_units(b.slots[3])  # Core casualty before any German order.
    close_unopposed_side(b.game)
    pending = pending_at_movement_start(b)
    assert b.slots[3].id not in pending and b.slots[4].id in pending
    obs = observation(b, pending)
    assert observation_space().contains(obs)
    assert obs["unit_status"][3:5].tolist() == [2, 1]
    assert obs["movement_remaining"][3:5].tolist() == [0, 7]
    assert obs["fire_flags"][3:5].tolist() == [[0, 0, 0, 0], [1, 0, 0, 0]]
    assert obs["reinforcement"][0, 3] == 2
    assert not action_mask(b, pending)[972:1296].any()
    assert action_mask(b, pending)[1312]
    assert bind_game(b.game, b.learner).slots == b.slots
    close_unopposed_side(b.game)
    assert b.slots[4].has_defensive_fire(b.opponent)


def test_full_arrival_mask_stacks_and_capacity(
        crossroads, close_unopposed_side):
    b = crossroads
    for _ in range(5):
        close_unopposed_side(b.game)
    pending = pending_at_movement_start(b)
    mask = action_mask(b, pending)
    assert mask[988] and mask[1312]
    assert observation(b, pending)["pending"].tolist() == [1] * 5
    b.slots[0].set_coords(1, 16)
    # Two arrivals fill the entry cell; a third friendly cannot enter it.
    assert not action_mask(b, pending)[16]
    for action in np.flatnonzero(mask[972:]) + 972:
        slot, plan = action_plan(b, pending - {b.slots[0].id}, action)
        assert slot in (3, 4)
        assert plan.unit is b.slots[slot]


def test_blocked_group_awaits_and_retries_only_on_cycle_wrap(
        crossroads, close_unopposed_side):
    b = crossroads
    b.slots[0].set_coords(0, 16)  # One occupant blocks both arrivals.
    for _ in range(4):
        close_unopposed_side(b.game)
    assert not b.reinforcement_group.entered
    assert len(b.game.reinforcements_deployer.game_log) == 1
    assert observation(b, set())["unit_status"][3:5].tolist() == [0, 0]
    close_unopposed_side(b.game)  # Handoff is not another deployment attempt.
    pending = pending_at_movement_start(b)
    assert len(b.game.reinforcements_deployer.game_log) == 1
    assert not action_mask(b, pending)[972:].any()
    close_unopposed_side(b.game)  # Wrap into 4: retry, still blocked.
    obs = observation(b, set())
    assert obs["reinforcement"].tolist() == [[3, 0, 16, 1]]
    assert len(b.game.reinforcements_deployer.game_log) == 2
    b.slots[0].set_coords(3, 15)
    close_unopposed_side(b.game)
    assert not b.reinforcement_group.entered
    close_unopposed_side(b.game)  # Wrap into 5: succeeds.
    assert b.game.turn_number == 5 and b.reinforcement_group.entered
    assert observation(b, set())["reinforcement"][0, 3] == 2
    b.game.board.remove_units([b.slots[3], b.slots[4]])
    obs = observation(b, set())
    assert obs["unit_status"][3:5].tolist() == [2, 2]
    assert obs["reinforcement"][0, 3] == 2
