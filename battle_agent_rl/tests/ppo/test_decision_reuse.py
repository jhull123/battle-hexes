"""Data-driven decision reuse, not trained-policy generalization."""

import pickle
import random

import numpy as np
import pytest

from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario_loader import load_scenario_data
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from battle_agent_rl.ppo.decision_actions import (
    action_mask, action_plan, pending_at_movement_start,
)
from battle_agent_rl.ppo.decision_contract import (
    action_space, observation_space,
)
from battle_agent_rl.ppo.decision_observation import observation
from battle_agent_rl.ppo.playable_scenario import LocalPlayer
from battle_agent_rl.ppo.scenario_task import ScenarioTask


def bind_fixture(scenario, learner_seat=0):
    """Use production task validation/binding; only fixture data differs."""
    task = ScenarioTask(scenario, learner_seat)
    players = [LocalPlayer(name, PlayerType.HUMAN, [])
               for name in ("Player 1", "Player 2")]
    game = GameCreator().build_game_components(scenario.to_core(), players)[-1]
    game.defensive_fire_resolver.rng = random.Random(81)
    return task, task.bind_game(game, players[learner_seat])


def assert_read_only_plans(binding, pending, mask):
    before = pickle.dumps((binding.game, pending))
    for action in np.flatnonzero(mask):
        slot, plan = action_plan(binding, pending, action)
        assert action_space(binding.spec).contains(action)
        assert plan.unit is binding.slots[slot]
        assert (plan.path[0].row, plan.path[0].column) == (
            plan.unit.get_coords())
        assert (plan.path[-1].row, plan.path[-1].column) == divmod(
            int(action) % binding.spec.cells, binding.spec.board_size[1])
    assert pickle.dumps((binding.game, pending)) == before


def test_rectangular_board_roster_spaces_and_action_mapping(small_scenario):
    _, b = bind_fixture(small_scenario)
    pending = set(pending_at_movement_start(b))
    assert pending == {"Scout"}
    obs = observation(b, pending)
    assert observation_space(b.spec).contains(obs)
    assert obs["positions"].shape == (4, 35)
    assert obs["positions"].argmax(axis=1).tolist() == [28, 0, 6, 0]
    assert obs["unit_status"].tolist() == [1, 0, 1, 0]
    assert obs["pending"].tolist() == [1, 0]
    assert obs["reinforcement"].tolist() == [[2, 0, 5, 0], [2, 4, 1, 0]]
    assert obs["remaining_cycles"].tolist() == [4]
    assert obs["terrain"][0].tolist() == [1, 1, 0]  # No terrain configured.
    assert obs["terrain"][21].tolist() == [2, 1, -1]
    assert obs["road_edges"][28, 0] == .5
    mask = action_mask(b, pending)
    assert mask.shape == (70,) and mask.dtype == np.bool_
    assert not mask[35:].any() and mask[28]
    reachable = b.game.board.get_reachable_hexes(
        b.slots[0], b.game.board.get_hex(4, 0), 3)
    assert set(np.flatnonzero(mask)) == {
        tile.row * 7 + tile.column for tile in reachable}
    assert_read_only_plans(b, pending, mask)
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
    assert obs["unit_status"].tolist() == [1, 1, 1, 0]
    assert obs["reinforcement"].tolist() == [[2, 0, 5, 0], [2, 4, 1, 2]]
    assert obs["fire_flags"][1].tolist() == [1, 0, 0, 0]
    assert np.flatnonzero(action_mask(b, {"Support"})).tolist() == [64]
    for _ in range(2):
        close_unopposed_side(b.game)
    assert observation(b, set())["reinforcement"][:, 3].tolist() == [1, 2]
    b.game.board.remove_units(b.slots[1])
    b.game.board.get_unit_by_id("Guard").set_coords(0, 6)
    for _ in range(2):
        close_unopposed_side(b.game)
    pending = pending_at_movement_start(b)
    obs = observation(b, pending)
    assert obs["unit_status"].tolist() == [1, 2, 1, 1]
    assert obs["reinforcement"][:, 3].tolist() == [2, 2]
    assert obs["remaining_cycles"].tolist() == [1]
    assert not obs["fire_flags"][3, 0]  # New opposing arrival cannot fire.
    assert not obs["positions"][1].any()
    assert obs["unit_stats"][1].tolist() == [2, 1, 0, 1]
    assert observation_space(b.spec).contains(obs)
    b.game.board.units = dict(reversed(list(b.game.board.units.items())))
    rebound = task.bind_game(b.game, b.learner)
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
    for action in (True, -1, 70, 28.0, np.array([28]), 64):
        with pytest.raises(ValueError):
            action_plan(b, pending, action)
        assert pickle.dumps((b.game, pending)) == before
    pending.remove("Scout")
    assert not action_mask(b, pending).any()
    assert not observation(b, pending)["pending"].any()
    pending.add("Scout")
    b.slots[0].current_turn_movement_points_remaining = 2
    before = pickle.dumps((b.game, pending))
    with pytest.raises(RuntimeError):
        action_plan(b, pending, 28)
    assert pickle.dumps((b.game, pending)) == before


def test_same_data_does_not_authorize_an_unconfigured_learner_seat(
        small_scenario):
    task, b = bind_fixture(small_scenario)
    with pytest.raises(ValueError):
        task.bind_game(b.game, b.opponent)
    other_task, other = bind_fixture(small_scenario, learner_seat=1)
    assert other_task.spec.learner_ids == ("Guard", "Reserve")
    assert other.learner is other.game.players[1]


@pytest.mark.parametrize("seat", [0, 1])
@pytest.mark.parametrize("source", ["loaded-data", "id-directory"])
def test_editor_json_runs_without_registration(
        small_scenario, tmp_path, close_unopposed_side, seat, source):
    """A new file uses the public loading/binding/decision path."""
    scenario_id = "editor-created-river-map"
    scenario = small_scenario.model_copy(update={
        "id": scenario_id, "name": "River map", "version": "editor-7"})
    path = tmp_path / f"{scenario_id}.json"
    path.write_text(scenario.model_dump_json(), encoding="utf-8")
    if source == "loaded-data":
        task = ScenarioTask(load_scenario_data(
            scenario_id, scenario_dir=tmp_path), learner_seat=seat)
    else:
        task = ScenarioTask.load(
            scenario_id, scenario_dir=tmp_path, learner_seat=seat)
    b = task.create_game(random.Random(81))
    assert task.scenario_id == b.game.scenario_id == scenario_id
    assert task.scenario_version == b.game.scenario_version == "editor-7"
    assert task.contract == "battle-hexes-unit-destination-live-v2"
    assert b.spec.board_size == (5, 7) and b.spec.turn_limit == 4
    assert len(b.slots) == 4 and b.spec.actions == 70
    assert b.spec.reinforcement_ids == ("blue-wave", "red-wave")
    assert b.scoring_player is b.game.players[0]
    assert b.learner is b.game.players[seat]
    if seat == 1:
        close_unopposed_side(b.game)
    assert_editor_decision(task, b)
    assert_editor_lifecycle(task, b, close_unopposed_side)


def assert_editor_decision(task, b):
    pending = set(pending_at_movement_start(b))
    obs = observation(b, pending)
    assert task.observation_space().contains(obs)
    assert task.action_space().n == 70
    assert obs["unit_status"].tolist() == [1, 0, 1, 0]
    assert obs["reinforcement"].tolist() == [[2, 0, 5, 0], [2, 4, 1, 0]]
    assert obs["remaining_cycles"].tolist() == [4]
    mask = action_mask(b, pending)
    unit = b.learner_slots[0]
    board = b.game.board
    reachable = board.get_reachable_hexes(
        unit, board.get_hex(*unit.get_coords()), unit.move)
    assert set(np.flatnonzero(mask)) == {
        tile.row * 7 + tile.column for tile in reachable}
    assert_read_only_plans(b, pending, mask)
    before = pickle.dumps((b.game, pending))
    with pytest.raises(ValueError):
        action_plan(b, pending, 70)
    assert pickle.dumps((b.game, pending)) == before
    hold = unit.row * 7 + unit.column
    _, plan = action_plan(b, pending, hold)
    b.game.apply_movement_plans([plan])
    pending.remove(unit.id)
    assert not action_mask(b, pending).any()


def assert_editor_lifecycle(task, b, close_unopposed_side):
    # Test drives core directly; no environment/turn orchestration is added.
    for _ in range(3):
        close_unopposed_side(b.game)
        if (b.game.turn_number == 2
                and b.game.get_current_player() is b.learner):
            break
    assert b.game.turn_number == 2
    pending = set(pending_at_movement_start(b))
    assert pending == set(b.spec.learner_ids)
    obs = observation(b, pending)
    assert obs["unit_status"].tolist() == [1] * 4
    assert obs["reinforcement"][:, 3].tolist() == [2, 2]
    assert task.observation_space().contains(obs)
    assert_read_only_plans(b, pending, action_mask(b, pending))
    original_slots = b.slots
    b.game.board.remove_units(b.learner_slots[1])
    rebound = task.bind_game(b.game, b.learner)
    assert rebound.slots == original_slots
    assert observation(rebound, pending)["unit_status"].tolist() == [
        1, 2, 1, 1]
    assert not action_mask(rebound, pending)[35:].any()
