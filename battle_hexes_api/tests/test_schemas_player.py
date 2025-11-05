"""Tests for the :mod:`battle_hexes_api.schemas.player` module."""

import pytest

from battle_hexes_api.schemas import FactionModel, PlayerModel
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction


def test_player_model_from_core_serializes_factions_and_type():
    faction = Faction(id="alpha", name="Alpha", color="#ff0000")
    player = Player(name="Alice", type=PlayerType.HUMAN, factions=[faction])

    model = PlayerModel.from_core(player)

    assert model.name == "Alice"
    assert model.type == PlayerType.HUMAN.value
    assert len(model.factions) == 1
    assert model.factions[0].model_dump() == {
        "id": "alpha",
        "name": "Alpha",
        "color": "#ff0000",
    }

    assert model.model_dump() == {
        "name": "Alice",
        "type": PlayerType.HUMAN.value,
        "factions": [
            {"id": "alpha", "name": "Alpha", "color": "#ff0000"},
        ],
    }


def test_player_model_to_core_round_trip():
    faction = Faction(id="beta", name="Beta", color="#00ff00")
    player = Player(name="Bob", type=PlayerType.CPU, factions=[faction])

    model = PlayerModel.from_core(player)
    rebuilt = model.to_core()

    assert rebuilt.name == "Bob"
    assert rebuilt.type == PlayerType.CPU
    assert rebuilt.factions == [faction]
    assert rebuilt is not player


def test_player_model_to_core_accepts_enum_type():
    faction = Faction(id="gamma", name="Gamma", color="#0000ff")
    faction_model = FactionModel.from_core(faction)

    model = PlayerModel(
        name="Carol",
        type=PlayerType.HUMAN,
        factions=[faction_model],
    )

    rebuilt = model.to_core()

    assert rebuilt.name == "Carol"
    assert rebuilt.type == PlayerType.HUMAN
    assert rebuilt.factions == [faction]


def test_player_model_to_core_invalid_type_raises_value_error():
    faction = Faction(id="zeta", name="Zeta", color="#abcdef")
    faction_model = FactionModel.from_core(faction)

    model = PlayerModel(
        name="Dana",
        type="Unknown",
        factions=[faction_model],
    )

    with pytest.raises(ValueError):
        model.to_core()
