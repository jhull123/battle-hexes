import json
from types import SimpleNamespace

import pytest

from battle_hexes_core.combat.combat_event import (
    CombatEvent,
    CombatOutcomeSnapshot,
    CombatTerrainSnapshot,
    CombatUnitSnapshot,
)
from battle_hexes_core.defensivefire.defensive_fire_event import (
    DefensiveFireEvent,
    DefensiveFireUnitSnapshot,
)
from battle_hexes_core.game.reinforcement import ReinforcementArrivalEvent
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import (
    GameStateCodec,
    SavedGameIncompatibleError,
    StoredGame,
)
from battle_hexes_api.schemas.game_log import game_log_from_game
from battle_hexes_core.scenario.scenario_loader import load_scenario_data


def stored(game, state, version):
    return StoredGame(
        game_id=str(game.id),
        version=1,
        state_schema_version=1,
        scenario_id=game.scenario_id,
        scenario_version=version,
        state=state,
        updated_at=1,
        expires_at=2,
    )


@pytest.mark.parametrize(
    "scenario_id",
    [
        "d_day_crossroads",
        "east_front_frozen_roadblock",
        "elim_1",
        "elim_2",
        "village_1",
    ],
)
def test_round_trip_is_canonical_and_detached(scenario_id):
    version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    codec = GameStateCodec()

    encoded = codec.encode(game, scenario_version=version)
    decoded = codec.decode(stored(game, encoded, version))

    assert codec.encode(decoded, scenario_version=version) == encoded
    assert decoded is not game
    assert decoded.board is not game.board
    assert all(player._board is decoded.board for player in decoded.players)
    assert json.loads(encoded)["state_schema_version"] == 1


def test_frozen_roadblock_elimination_without_objective_remains_persistable():
    scenario_id = "east_front_frozen_roadblock"
    scenario_version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    codec = GameStateCodec()
    game.turn_number = 2
    game.current_phase = "end_turn"
    game.board.remove_units(
        unit for unit in game.board.get_units()
        if unit.player.name == "Player 2"
    )
    scorer = ObjectiveScorer()
    scorer.recalculate_scenario_victory(game)
    assert game.get_game_status().state == "in_progress"
    assert not game.is_game_over()

    result = game.end_turn()

    assert result.game_status.state == "in_progress"
    assert result.current_player.name == "Player 2"
    assert game.current_phase == "movement"
    codec.encode(game, scenario_version=scenario_version)

    game.current_phase = "end_turn"
    scorer.recalculate_scenario_victory(game)
    final = game.end_turn()

    assert final.game_status.state == "completed"
    assert final.game_status.winner_player_name == "Player 2"
    assert game.current_player is None
    codec.encode(game, scenario_version=scenario_version)


def test_decode_rejects_metadata_mismatch():
    scenario_id = "elim_1"
    version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    codec = GameStateCodec()
    document = json.loads(codec.encode(game, scenario_version=version))
    document["scenario_version"] = "changed"
    state = json.dumps(document).encode()

    with pytest.raises(SavedGameIncompatibleError):
        codec.decode(stored(game, state, version))


def test_decode_rejects_unknown_fields():
    scenario_id = "elim_1"
    version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    codec = GameStateCodec()
    document = json.loads(codec.encode(game, scenario_version=version))
    document["unsafe"] = "ignored?"

    with pytest.raises(SavedGameIncompatibleError):
        codec.decode(
            stored(
                game,
                json.dumps(document).encode(),
                version,
            )
        )


@pytest.mark.parametrize("movement_points", [-1, 999])
def test_decode_rejects_invalid_movement_points(movement_points):
    scenario_id = "elim_1"
    version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    codec = GameStateCodec()
    document = json.loads(codec.encode(game, scenario_version=version))
    document["units"][0]["movement_points_remaining"] = movement_points

    with pytest.raises(SavedGameIncompatibleError):
        codec.decode(stored(game, json.dumps(document).encode(), version))


def test_decode_rejects_pending_combats_outside_combat_phase():
    scenario_id = "elim_1"
    version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    codec = GameStateCodec()
    document = json.loads(codec.encode(game, scenario_version=version))
    document["current_phase"] = "end_turn"
    document["pending_combats"] = [
        {
            "attacker_unit_ids": [document["active_unit_ids"][0]],
            "defender_unit_ids": [document["active_unit_ids"][1]],
        }
    ]

    with pytest.raises(SavedGameIncompatibleError):
        codec.decode(stored(game, json.dumps(document).encode(), version))


def test_round_trip_preserves_tuple_bearing_histories():
    scenario_id = "elim_1"
    version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    unit_ids = [str(unit.get_id()) for unit in game.board.get_units()]

    game.reinforcements_deployer.game_log.append(
        ReinforcementArrivalEvent(
            turn_number=1,
            player_name="Player 1",
            unit_count=1,
            entry_coordinate=(1, 2),
            outcome="blocked",
        )
    )
    game.combat_log.append(
        CombatEvent(
            turn_number=1,
            player_name="Player 1",
            attackers=(CombatUnitSnapshot("Infantry", 1, 1, 1),),
            defenders=(CombatUnitSnapshot("Infantry", 1, 1, 1),),
            base_odds=(1, 1),
            modified_odds=(1, 1),
            defender_terrain=CombatTerrainSnapshot("open", 0),
            die_roll=1,
            result=CombatOutcomeSnapshot("draw", "draw", "draw"),
            eliminated_units=(),
            retreated_units=(),
        )
    )
    game.defensive_fire_log.append(
        DefensiveFireEvent(
            turn_number=1,
            player_name="Player 1",
            firing_unit=DefensiveFireUnitSnapshot(unit_ids[0], "Infantry"),
            target_unit=DefensiveFireUnitSnapshot(unit_ids[1], "Infantry"),
            success_probability=0.5,
            random_roll=0.25,
            outcome="miss",
            summary="miss",
        )
    )

    codec = GameStateCodec()
    encoded = codec.encode(game, scenario_version=version)
    decoded = codec.decode(stored(game, encoded, version))

    payload = json.loads(encoded)
    assert isinstance(
        payload["reinforcement_history"][0]["entry_coordinate"], list
    )
    assert isinstance(payload["combat_history"][0]["attackers"], list)
    assert codec.encode(decoded, scenario_version=version) == encoded


def test_decoded_game_records_new_defensive_fire_in_authoritative_history():
    scenario_id = "elim_1"
    version = load_scenario_data(scenario_id).version
    game = GameCreator.create_sample_game(scenario_id, ["human", "random"])
    codec = GameStateCodec()
    decoded = codec.decode(stored(
        game, codec.encode(game, scenario_version=version), version
    ))
    firing_unit, target_unit = decoded.board.get_units()[:2]

    decoded.defensive_fire_event_recorder.record(
        [SimpleNamespace(
            firing_unit_id=str(firing_unit.get_id()),
            target_unit_id=str(target_unit.get_id()),
            probability=0.5,
            roll=0.75,
            outcome="no_effect",
            retreat_destination=None,
        )],
        target_unit,
        decoded.turn_number,
        decoded.current_player.name,
    )

    assert len(decoded.defensive_fire_log) == 1
    assert game_log_from_game(decoded)[0].events.defensive_fire[0].outcome == (
        "noEffect"
    )
    assert len(json.loads(codec.encode(
        decoded, scenario_version=version
    ))["defensive_fire_history"]) == 1
