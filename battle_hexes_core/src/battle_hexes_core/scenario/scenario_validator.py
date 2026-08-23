"""Validation for scenarios selected for play."""

from battle_hexes_core.scenario.scenario import Scenario
from battle_hexes_core.scenario.reinforcements_validator import (
    ReinforcementsValidator,
)


class ScenarioValidator:
    """Validate relationships between fields in a scenario definition."""

    def validate(self, scenario: Scenario) -> None:
        """Raise ``ValueError`` when ``scenario`` cannot be played safely."""
        self._validate_victory_scoring_side(scenario)
        ReinforcementsValidator().validate(scenario)

    def _validate_victory_scoring_side(self, scenario: Scenario) -> None:
        """Ensure the victory scoring side identifies a scenario faction."""
        victory = scenario.victory
        if victory is None:
            return

        faction_names = {
            identifier
            for faction in scenario.factions
            for identifier in (faction.id, faction.name)
        }
        if victory.scoring_side not in faction_names:
            raise ValueError(
                f"Scenario '{scenario.id}' victory scoring side "
                f"'{victory.scoring_side}' does not match a faction id or name"
            )
