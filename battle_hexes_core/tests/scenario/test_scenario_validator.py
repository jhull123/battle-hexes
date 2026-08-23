"""Tests for scenario relationship validation."""

import pytest

from battle_hexes_core.scenario.scenario import (
    Scenario,
    ScenarioFaction,
    ScenarioEntryLocation,
    ScenarioHexData,
    ScenarioReinforcement,
    ScenarioUnit,
    ScenarioVictory,
)
from battle_hexes_core.scenario.scenario_validator import ScenarioValidator


def _scenario(scoring_side: str | None) -> Scenario:
    victory = (
        ScenarioVictory(
            method="objective_control",
            scoring_side=scoring_side,
        )
        if scoring_side is not None
        else None
    )
    return Scenario(
        id="test-scenario",
        name="Test scenario",
        victory=victory,
        factions=(
            ScenarioFaction(
                id="allied-id",
                name="Allied Name",
                color="#123456",
                player="Player 1",
            ),
        ),
    )


@pytest.mark.parametrize("scoring_side", ["allied-id", "Allied Name"])
def test_accepts_scoring_side_matching_faction_id_or_name(scoring_side):
    ScenarioValidator().validate(_scenario(scoring_side))


def test_accepts_scenario_without_victory_configuration():
    ScenarioValidator().validate(_scenario(None))


def test_rejects_scoring_side_that_does_not_match_a_faction():
    scenario = _scenario("Unknown faction")

    with pytest.raises(
        ValueError,
        match=(
            "Scenario 'test-scenario' victory scoring side "
            "'Unknown faction' does not match a faction id or name"
        ),
    ):
        ScenarioValidator().validate(scenario)


def _reinforcement_scenario(**group_overrides):
    group_values = {
        "id": "reserve",
        "units": ("u1",),
        "arrival_turn": 2,
        "entry_location": ScenarioEntryLocation("fixed", (1, 1)),
    }
    group_values.update(group_overrides)
    return Scenario(
        id="reinforcement-test",
        name="Reinforcement test",
        board_size=(3, 3),
        factions=(
            ScenarioFaction("f1", "One", "#111", "Player 1"),
            ScenarioFaction("f2", "Two", "#222", "Player 2"),
        ),
        units=(
            ScenarioUnit("u1", "U1", "f1", "Infantry", 1, 1, 2),
            ScenarioUnit("u2", "U2", "f2", "Infantry", 1, 1, 2),
        ),
        reinforcements=(ScenarioReinforcement(**group_values),),
    )


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"id": "  "}, "must not be empty"),
        ({"units": ()}, "at least one unit"),
        ({"units": ("missing",)}, "Unknown reinforcement unit"),
        ({"units": ("u1", "u1")}, "repeats a unit id"),
        ({"units": ("u1", "u2")}, "belong to one player"),
        ({"arrival_turn": 0}, "arrival turn must be positive"),
        ({"entry_location": ScenarioEntryLocation("random", (1, 1))},
         "entry mode must be fixed"),
        ({"entry_location": ScenarioEntryLocation("fixed", (3, 0))},
         "out of bounds"),
    ],
)
def test_rejects_invalid_reinforcement_groups(overrides, message):
    with pytest.raises(ValueError, match=message):
        ScenarioValidator().validate(_reinforcement_scenario(**overrides))


def test_rejects_unit_assigned_to_board_and_reinforcement():
    scenario = _reinforcement_scenario()
    scenario = Scenario(
        **{
            **scenario.__dict__,
            "hex_data": (ScenarioHexData((0, 0), units=("u1",)),),
        }
    )

    with pytest.raises(ValueError, match="multiple deployment sources"):
        ScenarioValidator().validate(scenario)


def test_accepts_reinforcement_after_turn_limit():
    scenario = _reinforcement_scenario(arrival_turn=10)
    scenario = Scenario(**{**scenario.__dict__, "turn_limit": 3})

    ScenarioValidator().validate(scenario)


def test_rejects_duplicate_reinforcement_ids():
    scenario = _reinforcement_scenario()
    duplicate = ScenarioReinforcement(
        "reserve",
        ("u2",),
        3,
        ScenarioEntryLocation("fixed", (2, 2)),
    )
    scenario = Scenario(
        **{
            **scenario.__dict__,
            "reinforcements": scenario.reinforcements + (duplicate,),
        }
    )

    with pytest.raises(ValueError, match="Duplicate reinforcement id"):
        ScenarioValidator().validate(scenario)
