import json

import pytest

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
