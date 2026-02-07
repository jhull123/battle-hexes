from battle_hexes_core.game.hex import Hex
from battle_hexes_core.game.objective import Objective


def test_hex_defaults_to_no_objectives():
    hex_tile = Hex(1, 2)

    assert hex_tile.objectives == []


def test_hex_accepts_objectives():
    objective = Objective(coords=(1, 2), points=2, type="hold")
    hex_tile = Hex(1, 2, objectives=[objective])

    assert hex_tile.objectives == [objective]
