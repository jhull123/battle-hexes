"""Internal configuration probes, not additional supported PPO scenarios."""

from dataclasses import replace
import pickle
import random

import numpy as np
import pytest

from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario_loader import ScenarioData
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from battle_agent_rl.ppo.decision_actions import (
    action_mask, action_plan, pending_at_movement_start,
)
from battle_agent_rl.ppo.decision_contract import (
    ObservationBounds, ScenarioTask, action_space, observation_space,
)
from battle_agent_rl.ppo.decision_observation import observation
from battle_agent_rl.ppo.playable_scenario import LocalPlayer
from battle_agent_rl.ppo.scenario_binding import (
    bind_task, gameplay_fingerprint,
)


@pytest.fixture
def small_scenario():
    return ScenarioData.model_validate({
        "id": "internal-reuse-fixture", "version": "test-only",
        "name": "Not a supported task", "description": "Reuse probe",
        "board_size": [5, 7], "turn_limit": 4, "stacking_limit": 1,
        "victory": {"method": "objective_control", "scoring_side": "Red"},
        "factions": [
            {"id": color, "name": color, "color": color, "player": seat}
            for color, seat in (("Red", "Player 1"), ("Blue", "Player 2"))],
        "units": [
            {"id": name, "name": name, "faction": faction, "type": "Infantry",
             "attack": 2, "defense": 1, "movement": move}
            for name, faction, move in (("Scout", "Red", 3),
                                        ("Support", "Red", 0),
                                        ("Guard", "Blue", 2),
                                        ("Reserve", "Blue", 1))],
        "hex_data": [
            {"coords": [4, 0], "units": ["Scout"]},
            {"coords": [0, 6], "units": ["Guard"]},
            {"coords": [3, 0], "terrain": "rough"}],
        "terrain_types": {"rough": {
            "color": "gray", "move_cost": 2, "combat_odds_shift": -1}},
        "road_types": {"track": {"edge_move_cost": 0.5}},
        "roads": [{"type": "track", "path": [[4, 0], [3, 0]]}],
        # Deliberately not board order.
        "objectives": [{"coords": coords, "points": 1, "type": "occupy"}
                       for coords in ([3, 1], [1, 5])],
        "reinforcements": [
            {"id": name, "units": [unit], "arrival_turn": 2,
             "entry_location": {"mode": "fixed", "coords": coords}}
            for name, unit, coords in (("blue-wave", "Reserve", [0, 5]),
                                       ("red-wave", "Support", [4, 1]))],
    })


def bind_fixture(scenario, learner_seat=0):
    """Use production task validation/binding; only fixture data differs."""
    learner_ids = ("Support", "Scout") if learner_seat == 0 else (
        "Reserve", "Guard")
    opponent_ids = ("Reserve", "Guard") if learner_seat == 0 else (
        "Support", "Scout")
    roster = {unit.id for unit in scenario.units}
    task = ScenarioTask(
        scenario.id, scenario.version, gameplay_fingerprint(scenario),
        "internal-reuse-test-only", learner_seat,
        tuple(u for u in learner_ids if u in roster),
        tuple(u for u in opponent_ids if u in roster),
        ObservationBounds(3, 3, -1, 2, .5, 1, 2, 6))
    players = [LocalPlayer(name, PlayerType.HUMAN, [])
               for name in ("Player 1", "Player 2")]
    game = GameCreator().build_game_components(scenario.to_core(), players)[-1]
    game.defensive_fire_resolver.rng = random.Random(81)
    return task, bind_task(game, players[learner_seat], task, scenario)


def test_rectangular_board_roster_spaces_and_action_mapping(small_scenario):
    _, b = bind_fixture(small_scenario)
    pending = set(pending_at_movement_start(b))
    assert pending == {"Scout"}  # Slot 0 is reserved, not the first actor.
    obs = observation(b, pending)
    assert observation_space(b.spec).contains(obs)
    assert obs["positions"].shape == (4, 35)
    assert obs["positions"].argmax(axis=1).tolist() == [0, 28, 0, 6]
    assert obs["unit_status"].tolist() == [0, 1, 0, 1]
    assert obs["pending"].tolist() == [0, 1]
    assert obs["reinforcement"].tolist() == [[2, 0, 5, 0], [2, 4, 1, 0]]
    assert obs["remaining_cycles"].tolist() == [4]
    assert obs["terrain"][0].tolist() == [1, 1, 0]  # No terrain configured.
    assert obs["terrain"][21].tolist() == [2, 1, -1]
    assert obs["road_edges"][28, 0] == .5
    mask = action_mask(b, pending)
    assert mask.shape == (70,) and mask.dtype == np.bool_
    assert not mask[:35].any() and mask[63]
    reachable = b.game.board.get_reachable_hexes(
        b.slots[1], b.game.board.get_hex(4, 0), 3)
    assert set(np.flatnonzero(mask)) == {
        35 + tile.row * 7 + tile.column for tile in reachable}
    before = pickle.dumps((b.game, pending))
    for action in np.flatnonzero(mask):
        slot, plan = action_plan(b, pending, action)
        assert action_space(b.spec).contains(action)
        assert slot == 1 and plan.unit.id == "Scout"
        assert (plan.path[-1].row, plan.path[-1].column) == divmod(
            int(action) - 35, 7)
    assert pickle.dumps((b.game, pending)) == before
    again = observation(b, pending)
    for key in obs:
        assert not np.shares_memory(obs[key], again[key])
        np.testing.assert_array_equal(obs[key], again[key])


@pytest.mark.parametrize("seat", [0, 1])
@pytest.mark.parametrize("scoring_side", ["Red", "Blue"])
def test_scoring_side_is_not_a_synonym_for_opponent(
        small_scenario, close_unopposed_side, seat, scoring_side):
    victory = small_scenario.victory.model_copy(
        update={"scoring_side": scoring_side})
    scenario = small_scenario.model_copy(update={"victory": victory})
    _, b = bind_fixture(scenario, seat)
    red = b.game.board.get_unit_by_id("Scout")
    red.set_coords(3, 1)
    # Readiness is relative to learner, not to the core scoring side.
    red.current_turn_movement_points_remaining = 1
    obs = observation(b, set())
    red_slot = next(i for i, u in enumerate(b.slots) if u.id == "Scout")
    assert obs["fire_flags"][red_slot, 0] == (seat != 0)
    assert obs["objective_control"].tolist() == (
        [1, 0] if scoring_side == "Red" else [0, 0])
    assert obs["scores"].tolist() == [0, 0]  # Encoding never scores.
    ObjectiveScorer().recalculate_scenario_victory(b.game)
    expected_core_scores = [1, 1] if scoring_side == "Red" else [2, 0]
    assert observation(b, set())["scores"].tolist() == (
        expected_core_scores if seat == 0 else expected_core_scores[::-1])
    assert b.scoring_player is b.game.players[scoring_side == "Blue"]
    if seat == 1:
        assert not action_mask(b, {"Guard"}).any()
        close_unopposed_side(b.game)
    assert pending_at_movement_start(b) == (
        {"Scout"} if seat == 0 else {"Guard"})


def test_multiple_groups_lifecycle_and_core_pending_status(
        small_scenario, close_unopposed_side):
    task, b = bind_fixture(small_scenario)
    b.game.board.get_unit_by_id("Guard").set_coords(0, 5)
    for _ in range(2):
        close_unopposed_side(b.game)
    assert b.game.turn_number == 2
    obs = observation(b, pending_at_movement_start(b))
    assert obs["unit_status"].tolist() == [1, 1, 0, 1]
    assert obs["reinforcement"].tolist() == [[2, 0, 5, 0], [2, 4, 1, 2]]
    assert obs["fire_flags"][0].tolist() == [1, 0, 0, 0]
    assert np.flatnonzero(action_mask(b, {"Support"})).tolist() == [29]
    for _ in range(2):
        close_unopposed_side(b.game)
    assert observation(b, set())["reinforcement"][:, 3].tolist() == [1, 2]
    b.game.board.remove_units(b.slots[0])
    b.game.board.get_unit_by_id("Guard").set_coords(0, 6)
    for _ in range(2):
        close_unopposed_side(b.game)
    pending = pending_at_movement_start(b)
    obs = observation(b, pending)
    assert obs["unit_status"].tolist() == [2, 1, 1, 1]
    assert obs["reinforcement"][:, 3].tolist() == [2, 2]
    assert obs["remaining_cycles"].tolist() == [1]
    assert not obs["fire_flags"][2, 0]  # New opposing arrival cannot fire.
    assert not obs["positions"][0].any()
    assert obs["unit_stats"][0].tolist() == [2, 1, 0, 1]
    assert observation_space(b.spec).contains(obs)
    b.game.board.units = dict(reversed(list(b.game.board.units.items())))
    rebound = bind_task(b.game, b.learner, task, small_scenario)
    assert rebound.slots == b.slots
    assert pending == {"Scout"}
    for key, value in obs.items():
        np.testing.assert_array_equal(
            observation(rebound, pending)[key], value)


def test_no_groups_or_objectives_have_empty_arrays(small_scenario):
    scenario = small_scenario.model_copy(update={
        "reinforcements": [], "objectives": [], "victory": None,
        "units": [u for u in small_scenario.units
                  if u.id in ("Scout", "Guard")],
    })
    _, b = bind_fixture(scenario)
    obs = observation(b, pending_at_movement_start(b))
    assert b.scoring_player is None and b.reinforcement_groups == ()
    assert obs["reinforcement"].shape == (0, 4)
    assert obs["objective_control"].shape == (0,)
    assert obs["positions"].shape == (2, 35)
    assert action_space(b.spec).n == 35
    assert observation_space(b.spec).contains(obs)


def test_entered_groups_do_not_shift_pending_group_status(
        small_scenario, close_unopposed_side):
    _, b = bind_fixture(small_scenario)
    b.game.board.get_unit_by_id("Scout").set_coords(4, 1)
    for _ in range(2):
        close_unopposed_side(b.game)
    assert observation(b, set())["reinforcement"][:, 3].tolist() == [2, 0]
    for _ in range(2):
        close_unopposed_side(b.game)
    assert observation(b, set())["reinforcement"][:, 3].tolist() == [2, 1]


def test_reused_validation_is_non_mutating(small_scenario):
    _, b = bind_fixture(small_scenario)
    pending = set(pending_at_movement_start(b))
    before = pickle.dumps((b.game, pending))
    for action in (True, -1, 70, 63.0, np.array([63]), 29):
        with pytest.raises(ValueError):
            action_plan(b, pending, action)
        assert pickle.dumps((b.game, pending)) == before
    pending.remove("Scout")
    assert not action_mask(b, pending).any()
    assert not observation(b, pending)["pending"].any()
    pending.add("Scout")
    b.slots[1].current_turn_movement_points_remaining = 2
    before = pickle.dumps((b.game, pending))
    with pytest.raises(RuntimeError):
        action_plan(b, pending, 63)
    assert pickle.dumps((b.game, pending)) == before


def test_same_data_does_not_authorize_an_unconfigured_learner_seat(
        small_scenario):
    task, b = bind_fixture(small_scenario)
    with pytest.raises(ValueError):
        bind_task(b.game, b.opponent, task, small_scenario)
    with pytest.raises(ValueError):
        bind_task(b.game, b.opponent, replace(task, learner_seat=1),
                  small_scenario)  # Ordered roster owners must agree too.
