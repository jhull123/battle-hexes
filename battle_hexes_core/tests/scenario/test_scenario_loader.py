import json
from pathlib import Path

import pytest

from battle_hexes_core.scenario.scenario_loader import (
    iter_scenario_data,
    iter_scenarios,
    load_scenario,
    load_scenario_data,
)


def _scenario_dir() -> Path:
    return (
        Path(__file__)
        .resolve()
        .parents[2]
        / "src"
        / "battle_hexes_core"
        / "scenarios"
    )


def test_load_scenario_data_from_directory():
    scenario = load_scenario_data(
        "elim_1", scenario_dir=_scenario_dir()
    )

    assert scenario.id == "elim_1"
    assert scenario.board_size == (10, 10)
    assert scenario.factions[0].name == "Red Faction"
    assert scenario.units[0].movement == 6


def test_load_scenario_data_raises_for_mismatched_id(tmp_path):
    payload_path = _scenario_dir() / "elim_1.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    scenario_path = tmp_path / "expected.json"
    scenario_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match file contents"):
        load_scenario_data("expected", scenario_dir=tmp_path)


def test_load_scenario_converts_core_types():
    scenario = load_scenario(
        "elim_1", scenario_dir=_scenario_dir()
    )

    assert scenario.terrain_default == "open"
    assert scenario.terrain_types["open"].color == "#C6AA5C"
    assert scenario.hex_data[0].coords == (5, 5)
    assert scenario.hex_data[1].units == ("red_unit_1",)
    assert scenario.hex_data[0].objectives[0].type == "hold"
    assert scenario.hex_data[0].objectives[0].points == 3


def test_load_scenario_assigns_objectives_to_hexes():
    scenario = load_scenario(
        "elim_2", scenario_dir=_scenario_dir()
    )

    objective_hex = next(
        hex_entry
        for hex_entry in scenario.hex_data
        if hex_entry.coords == (2, 3)
    )
    assert objective_hex.terrain is None
    assert objective_hex.units is None
    assert objective_hex.objectives[0].type == "hold"
    assert objective_hex.objectives[0].points == 1


def test_iterators_yield_all_scenarios():
    scenario_ids = {
        scenario.id
        for scenario in iter_scenario_data(scenario_dir=_scenario_dir())
    }
    core_ids = {
        scenario.id
        for scenario in iter_scenarios(scenario_dir=_scenario_dir())
    }

    assert scenario_ids == {"elim_1", "elim_2", "village_1"}
    assert core_ids == {"elim_1", "elim_2", "village_1"}
