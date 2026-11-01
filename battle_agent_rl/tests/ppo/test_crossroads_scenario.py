"""Scenario fingerprint, live compatibility and insertion-independent slots."""

import random
from dataclasses import replace

import pytest

from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.scenario.scenario_loader import load_scenario_data

from battle_agent_rl.ppo.crossroads_contract import SLOT_IDS
from battle_agent_rl.ppo.playable_scenario import LocalPlayer
from battle_agent_rl.ppo.crossroads_scenario import (
    GAMEPLAY_SHA256, bind_game, create_game,
    slots_for_game, validate_scenario,
)
from battle_agent_rl.ppo.scenario_binding import gameplay_fingerprint


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
    assert gameplay_fingerprint(validate_scenario()) == GAMEPLAY_SHA256


@pytest.mark.parametrize("field,value", [
    ("id", "ppo_9x9_experimental"), ("version", "2"),
    ("board_size", (9, 9)), ("turn_limit", 7), ("stacking_limit", 1),
    ("units", []), ("reinforcements", []), ("roads", []),
    ("objectives", []), ("terrain_default", "rough"),
])
def test_reject_changed_scenario(field, value):
    scenario = load_scenario_data("d_day_crossroads")
    changed = scenario.model_copy(update={field: value})
    with pytest.raises(ValueError):
        validate_scenario(changed)


@pytest.mark.parametrize("field,change", [
    ("victory", {"scoring_side": "Wehrmacht"}),
    ("defensive_fire", {"base_probability": 0.5}),
])
def test_reject_changed_rule_objects(field, change):
    scenario = load_scenario_data("d_day_crossroads")
    changed = getattr(scenario, field).model_copy(update=change)
    with pytest.raises(ValueError):
        validate_scenario(scenario.model_copy(update={field: changed}))


@pytest.mark.parametrize("kind", ["unit", "terrain", "arrival", "side"])
def test_nested_gameplay_changes_are_not_just_metadata(kind):
    scenario = load_scenario_data("d_day_crossroads")
    payload = scenario.model_dump(mode="json")
    if kind == "unit":
        payload["units"][0]["defensive_fire_modifier"] = 1.1
    elif kind == "terrain":
        payload["terrain_types"]["forest"]["move_cost"] = 2
    elif kind == "arrival":
        payload["reinforcements"][0]["entry_location"]["coords"] = [0, 15]
    else:
        payload["factions"][0]["player"] = "Player 2"
    with pytest.raises(ValueError):
        validate_scenario(type(scenario).model_validate(payload))


def test_presentation_and_insertion_order_do_not_define_identity():
    scenario = validate_scenario()
    changed = scenario.model_copy(update={
        "name": "Display name", "description": "Display description",
        "units": list(reversed(scenario.units)),
        "hex_data": list(reversed(scenario.hex_data)),
        "factions": list(reversed(scenario.factions)),
    })
    assert validate_scenario(changed) is changed
    game = GameCreator().build_game_components(
        changed.to_core(), [LocalPlayer(name, PlayerType.HUMAN, [])
                            for name in ("Player 1", "Player 2")])[-1]
    # The core builder does not attach a scenario_version: ordinary games bind.
    bound = bind_game(game, game.players[1], changed)
    assert tuple(u.id for u in bound.slots) == SLOT_IDS
    assert bound.objective_coords == ((2, 3), (3, 15), (6, 9))


@pytest.mark.parametrize("mutation", [
    "side", "roster", "stats", "owner", "fire", "terrain", "roads",
    "objectives", "reinforcement", "turn_limit", "version", "victory",
])
def test_live_binding_rejects_wrong_side_or_gameplay(crossroads, mutation):
    game = crossroads.game
    learner = crossroads.learner
    if mutation == "side":
        learner = crossroads.opponent
    elif mutation == "roster":
        game.board.add_unit(game.board.get_units()[0], 1, 1)
        game.board.get_units()[0].id = "foreign"
        game.board.add_unit(game.board.get_units()[0], 1, 1)
    elif mutation == "stats":
        crossroads.slots[0].attack = 7
    elif mutation == "owner":
        crossroads.slots[0]._player = crossroads.opponent
    elif mutation == "fire":
        game.set_defensive_fire_settings(replace(
            game.defensive_fire_resolver.settings, base_probability=0.5))
    elif mutation == "terrain":
        game.board.get_hex(0, 0).set_terrain(None)
    elif mutation == "roads":
        game.board.set_road_paths(())
    elif mutation == "objectives":
        game.board.get_hex(2, 3).objectives.clear()
    elif mutation == "reinforcement":
        crossroads.reinforcement_groups[0].arrival_turn = 4
    elif mutation == "turn_limit":
        game.turn_limit = 9
    elif mutation == "version":
        game.scenario_version = "2"
    elif mutation == "victory":
        game.victory = None
    with pytest.raises(ValueError):
        bind_game(game, learner)


def test_rebind_keeps_eliminated_and_reserved_slots(crossroads):
    game = crossroads.game
    game.board.remove_units(crossroads.slots[0])
    game.board.units = dict(reversed(list(game.board.units.items())))
    rebound = bind_game(game, crossroads.learner)
    assert rebound.slots == crossroads.slots
    assert slots_for_game(game) == crossroads.slots
    rng = random.Random(91)
    before = rng.getstate()
    create_game(rng)
    assert rng.getstate() == before
