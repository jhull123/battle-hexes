import json

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

from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import (
    GameStateCodec,
    SavedGameIncompatibleError,
    StoredGame,
)
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
