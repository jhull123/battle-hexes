"""Tests for scenario relationship validation."""

import pytest

from battle_hexes_core.scenario.scenario import (
    Scenario,
    ScenarioFaction,
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
