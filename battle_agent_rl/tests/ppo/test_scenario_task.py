"""Supported interface variations and actionable unsupported-config errors."""

from dataclasses import replace
import random

import pytest

from battle_hexes_core.scenario.scenario_loader import ScenarioData
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from battle_agent_rl.ppo.crossroads_scenario import (
    TASK, bind_game, create_game,
)
from battle_agent_rl.ppo.decision_contract import observation_space
from battle_agent_rl.ppo.decision_observation import observation
from battle_agent_rl.ppo.scenario_task import ScenarioTask


@pytest.mark.parametrize("field,value,match", [
    ("turn_limit", None, "horizon"),
    ("turn_limit", 0, "horizon"),
    ("turn_limit", 2147483648, "horizon"),
    ("board_size", [0, 18], "dimensions"),
    ("board_size", [18, 2147483648], "dimensions"),
    ("victory", None, "scoring-side"),
    ("victory", {"method": "unknown", "scoring_side": "Airborne"},
     "scoring-side"),
])
def test_unsupported_dimensions_or_objective_rules(field, value, match):
    payload = TASK.scenario.model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValueError, match=match):
        create_game(random.Random(0), ScenarioData.model_validate(payload))


@pytest.mark.parametrize("kind,value,match", [
    ("movement", 128, "movement"),
    ("movement", -1, "unit stats"),
    ("attack", -1, "unit stats"),
    ("defensive_fire_modifier", float("nan"), "unit stats"),
    ("defensive_fire_modifier", float("inf"), "unit stats"),
    ("defensive_fire_modifier", 1e39, "unit stats"),
])
def test_unsupported_unit_numeric_inputs(kind, value, match):
    payload = TASK.scenario.model_dump(mode="json")
    payload["units"][-1][kind] = value  # Undeployed reserves count too.
    with pytest.raises(ValueError, match=match):
        create_game(random.Random(0), ScenarioData.model_validate(payload))


@pytest.mark.parametrize("kind,match", [
    ("score-overflow", "scores"),
    ("negative-points", "objective points"),
    ("point-overflow", "objective points"),
    ("terrain", "terrain"),
    ("road", "road costs"),
    ("missing-unit", "roster"),
    ("duplicate-unit", "unique unit"),
    ("unknown-owner", "Unknown player"),
    ("empty-side", "nonempty roster"),
])
def test_unsupported_scenario_configurations(kind, match):
    payload = TASK.scenario.model_dump(mode="json")
    if kind == "score-overflow":
        payload["objectives"] = [
            {"coords": divmod(i, 18), "points": 0, "type": "occupy"}
            for i in range(128)]
    elif kind == "negative-points":
        payload["objectives"][0]["points"] = -1
    elif kind == "point-overflow":
        payload["objectives"][0]["points"] = 128
    elif kind == "terrain":
        payload["terrain_types"]["open"]["move_cost"] = 0
    elif kind == "road":
        payload["road_types"]["secondary"]["edge_move_cost"] = float("inf")
    elif kind == "missing-unit":
        payload["units"].append(dict(payload["units"][0], id="Unplaced"))
    elif kind == "duplicate-unit":
        payload["units"].append(payload["units"][0])
    elif kind == "unknown-owner":
        payload["factions"][0]["player"] = "Player 3"
    elif kind == "empty-side":
        payload["factions"][0]["player"] = "Player 2"
    with pytest.raises(ValueError, match=match):
        create_game(random.Random(0), ScenarioData.model_validate(payload))


def test_interface_compatible_live_variation_is_not_rejected(crossroads):
    b = crossroads
    b.game.scenario_id = "metadata-is-not-a-gameplay-lock"
    b.game.scenario_version = "new"
    b.game.set_defensive_fire_settings(replace(
        b.game.defensive_fire_resolver.settings, base_probability=.5))
    b.slots[0].attack = 6  # Within configured observation bounds.
    b.game.board.get_hex(0, 0).set_terrain(None)
    b.game.board.set_road_paths(())
    b.reinforcement_groups[0].arrival_turn = 5
    rebound = bind_game(b.game, b.learner)
    assert rebound.slots == b.slots
    inputs = observation(rebound, set())
    assert observation_space(rebound.spec).contains(inputs)


def test_slots_are_derived_before_any_arrival_even_if_reserve_sorts_first():
    payload = TASK.scenario.model_dump(mode="json")
    payload["units"][-1]["id"] = "00 reserve"
    payload["reinforcements"][0]["units"][0] = "00 reserve"
    b = create_game(random.Random(0), ScenarioData.model_validate(payload))
    assert b.slots[0].id == "00 reserve"
    assert b.slots[0].get_coords() is None
    assert observation(b, set())["unit_status"][0] == 0


def test_task_derives_default_spaces_from_new_loaded_definition():
    scenario = TASK.scenario.model_copy(update={
        "turn_limit": 12, "version": "3"})
    task = ScenarioTask(scenario, TASK.learner_seat, TASK.contract)
    assert task.scenario_version == "3" and task.spec.turn_limit == 12
    space = observation_space(task.spec)["remaining_cycles"]
    assert space.high.tolist() == [12]


def test_invalid_learner_seat_fails_clearly():
    with pytest.raises(ValueError, match="learner seat"):
        ScenarioTask(TASK.scenario, 2, TASK.contract)


def test_bounds_include_stacked_objectives_and_late_arrivals():
    payload = TASK.scenario.model_dump(mode="json")
    payload["objectives"].append(dict(payload["objectives"][0], points=2))
    payload["reinforcements"][0]["arrival_turn"] = 40
    b = create_game(random.Random(0), ScenarioData.model_validate(payload))
    assert b.spec.bounds.objective_points_high == 3
    assert b.spec.bounds.score_high == 4
    assert b.spec.bounds.reinforcement_high == 40
    assert observation_space(b.spec).contains(observation(b, set()))


def test_zero_point_objectives_still_count_in_core_scores():
    payload = TASK.scenario.model_dump(mode="json")
    for objective in payload["objectives"]:
        objective["points"] = 0
    b = create_game(random.Random(0), ScenarioData.model_validate(payload))
    ObjectiveScorer().recalculate_scenario_victory(b.game)
    obs = observation(b, set())
    assert b.spec.bounds.objective_points_high == 0
    assert b.spec.bounds.score_high == 3
    assert obs["scores"].tolist() == [3, 0]
    assert observation_space(b.spec).contains(obs)
