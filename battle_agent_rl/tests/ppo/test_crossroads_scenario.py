"""Scenario-derived configuration and stable complete-roster identities."""

import random

import numpy as np
import pytest

from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.scenario.scenario_loader import (
    ScenarioData, load_scenario_data,
)
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from battle_agent_rl.ppo.playable_scenario import LocalPlayer
from battle_agent_rl.ppo.scenario_task import ScenarioTask
from battle_agent_rl.ppo.decision_actions import (
    action_mask, action_plan, pending_at_movement_start,
)
from battle_agent_rl.ppo.decision_contract import observation_space
from battle_agent_rl.ppo.decision_observation import observation


SLOT_IDS = (
    "A / Inf. Zug", "B / Inf. Zug", "Crossroads Feldwache", "MG Trupp A",
    "StuG. III Zug A", *(f"Airborne Inf. {c}" for c in "ABCDEF"),
)


def test_raw_game_is_actual_airborne_first_core_state(crossroads):
    game = crossroads.game
    assert game.scenario_id == "d_day_crossroads"
    assert game.scenario_version == "1"
    assert game.get_current_player() is crossroads.opponent
    assert game.players == [crossroads.opponent, crossroads.learner]
    assert game.turn_number == 1 and game.turn_limit == 8
    assert game.board.stacking_limit == 2
    assert (game.board.rows, game.board.columns) == (18, 18)
    assert tuple(u.id for u in crossroads.slots) == SLOT_IDS
    assert len(game.board.get_units()) == 9
    assert len(game.board.get_objectives()) == 3
    assert [u.get_coords() for u in crossroads.slots[:5]] == [
        (3, 15), (4, 5), (6, 9), None, None]


def test_presentation_and_insertion_order_do_not_define_slots(crossroads_task):
    scenario = crossroads_task.scenario
    changed = scenario.model_copy(update={
        "name": "Display name", "description": "Display description",
        "units": list(reversed(scenario.units)),
        "hex_data": list(reversed(scenario.hex_data)),
        "factions": list(reversed(scenario.factions)),
    })
    task = ScenarioTask(changed, learner_seat=1)
    game = GameCreator().build_game_components(
        changed.to_core(), [LocalPlayer(name, PlayerType.HUMAN, [])
                            for name in ("Player 1", "Player 2")])[-1]
    bound = task.bind_game(game, game.players[1])
    assert tuple(u.id for u in bound.slots) == SLOT_IDS
    assert bound.objective_coords == ((2, 3), (3, 15), (6, 9))


@pytest.fixture
def varied_scenario():
    payload = load_scenario_data("d_day_crossroads").model_dump(mode="json")
    payload.update(id="internal-crossroads-variation", version="2",
                   board_size=[19, 20], turn_limit=11, stacking_limit=3)
    payload["units"][6].update(attack=12, movement=9)
    payload["units"][0]["faction"] = "Wehrmacht"  # Ownership from core.
    payload["units"].append({
        "id": "Additional reserve", "name": "Reserve", "faction": "Wehrmacht",
        "type": "Infantry", "attack": 1, "defense": 2, "movement": 2})
    payload["reinforcements"].append({
        "id": "second-wave", "units": ["Additional reserve"],
        "arrival_turn": 10,
        "entry_location": {"mode": "fixed", "coords": [18, 19]}})
    payload["reinforcements"][0]["arrival_turn"] = 4
    payload["objectives"].append({
        "coords": [18, 0], "points": 4, "type": "occupy"})
    payload["terrain_types"]["rough"].update(move_cost=5, combat_odds_shift=-4)
    payload["road_types"]["secondary"]["edge_move_cost"] = 2.5
    payload["defensive_fire"]["base_probability"] = .5
    payload["victory"]["scoring_side"] = "Wehrmacht"
    return ScenarioData.model_validate(payload)


def test_variation_uses_production_task_interface(
        varied_scenario, close_unopposed_side, crossroads_task):
    scenario = varied_scenario
    task = ScenarioTask(scenario, learner_seat=1)
    b = task.create_game(random.Random(91))
    assert b.spec.board_size == (19, 20) and b.spec.turn_limit == 11
    assert len(b.spec.learner_ids) == 7 and len(b.spec.opponent_ids) == 5
    assert b.spec.learner_ids == tuple(sorted(b.spec.learner_ids))
    assert "Additional reserve" in b.spec.learner_ids
    assert "Airborne Inf. A" in b.spec.learner_ids
    assert b.spec.bounds.unit_stats_high == 12
    assert b.spec.bounds.movement_high == 9
    assert b.spec.bounds.terrain_low == -4
    assert b.spec.bounds.terrain_high == 5
    assert b.spec.bounds.road_high == 2.5
    assert b.spec.bounds.objective_points_high == 4
    assert b.spec.bounds.score_high == 4
    assert b.spec.bounds.reinforcement_high == 19
    assert b.scoring_player is b.learner
    close_unopposed_side(b.game)
    pending = pending_at_movement_start(b)
    ObjectiveScorer().recalculate_scenario_victory(b.game)
    obs = observation(b, pending)
    assert obs["scores"].tolist() == [2, 2]
    assert obs["positions"].shape == (12, 380)
    assert obs["objective_control"].shape == (4,)
    assert obs["reinforcement"].tolist() == [[4, 0, 16, 0], [10, 18, 19, 0]]
    assert obs["remaining_cycles"].tolist() == [11]
    assert observation_space(b.spec).contains(obs)
    assert task.observation_space() == observation_space(b.spec)
    assert task.action_space().n == 7 * 380
    for action in np.flatnonzero(action_mask(b, pending)):
        slot, plan = action_plan(b, pending, action)
        assert plan.unit is b.slots[slot]
    assert task.bind_game(b.game, b.learner).slots == b.slots
    # Independently loaded tasks retain their own configuration.
    assert crossroads_task.spec.board_size == (18, 18)


@pytest.mark.parametrize("mutation,match", [
    ("side", "seat"), ("roster", "roster"), ("stats", "bound"),
    ("owner", "owners"), ("objectives", "objective"),
    ("reinforcement", "reinforcement"), ("turn_limit", "horizon"),
    ("victory", "scoring-side"),
])
def test_live_binding_rejects_interface_mismatches(
        crossroads, crossroads_task, mutation, match):
    game, learner = crossroads.game, crossroads.learner
    if mutation == "side":
        learner = crossroads.opponent
    elif mutation == "roster":
        game.board.get_units()[0].id = "foreign"
    elif mutation == "stats":
        crossroads.slots[0].attack = 8
    elif mutation == "owner":
        crossroads.slots[0]._player = crossroads.opponent
    elif mutation == "objectives":
        game.board.get_hex(2, 3).objectives.clear()
    elif mutation == "reinforcement":
        crossroads.reinforcement_groups[0].id = "unknown"
    elif mutation == "turn_limit":
        game.turn_limit = 9
    elif mutation == "victory":
        game.victory = None
    with pytest.raises(ValueError, match=match):
        crossroads_task.bind_game(game, learner)


def test_rebind_keeps_eliminated_and_reserved_slots(
        crossroads, crossroads_task):
    game = crossroads.game
    game.board.remove_units(crossroads.slots[0])
    game.board.units = dict(reversed(list(game.board.units.items())))
    rebound = crossroads_task.bind_game(game, crossroads.learner)
    assert rebound.slots == crossroads.slots
    rng = random.Random(91)
    before = rng.getstate()
    crossroads_task.create_game(rng)
    assert rng.getstate() == before
