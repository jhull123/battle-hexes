"""Tests for creating runtime reinforcement groups."""

from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.gamecreator.reinforcements_creator import (
    ReinforcementsCreator,
)
from battle_hexes_core.scenario.scenario import (
    Scenario,
    ScenarioEntryLocation,
    ScenarioReinforcement,
    ScenarioUnit,
)
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


def test_builds_runtime_group_and_units_from_scenario_data():
    faction = Faction("f1", "Faction", "#123")
    player = Player("Player 1", PlayerType.HUMAN, [faction])
    unit = Unit(
        "reserve",
        "Reserve",
        faction,
        player,
        "Infantry",
        2,
        3,
        4,
    )
    unit.defensive_fire_modifier = 0.5
    scenario = Scenario(
        id="scenario",
        name="Scenario",
        units=(
            ScenarioUnit(
                "reserve",
                "Reserve",
                "f1",
                "Infantry",
                2,
                3,
                4,
                defensive_fire_modifier=0.5,
            ),
        ),
        reinforcements=(
            ScenarioReinforcement(
                "group",
                ("reserve",),
                3,
                ScenarioEntryLocation("fixed", (1, 2)),
            ),
        ),
    )
    creator = ReinforcementsCreator(lambda *_: unit)

    groups = creator.build_reinforcements(
        scenario,
        {"f1": faction},
        {"f1": player},
    )

    assert len(groups) == 1
    assert groups[0].id == "group"
    assert groups[0].arrival_turn == 3
    assert groups[0].coords == (1, 2)
    assert groups[0].units == (unit,)
    assert not unit.defensive_fire_available


def test_returns_no_groups_when_scenario_has_no_reinforcements():
    scenario = Scenario(id="scenario", name="Scenario")
    creator = ReinforcementsCreator(lambda *_: None)

    groups = creator.build_reinforcements(scenario, {}, {})

    assert groups == []
