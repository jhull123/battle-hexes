"""Create runtime reinforcement groups from scenario definitions."""

from collections.abc import Callable

from battle_hexes_core.game.player import Player
from battle_hexes_core.game.reinforcement import ReinforcementGroup
from battle_hexes_core.scenario.scenario import Scenario, ScenarioUnit
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

UnitBuilder = Callable[[ScenarioUnit, Faction, Player], Unit]


class ReinforcementsCreator:
    """Build off-board runtime units for scenario reinforcement groups."""

    def __init__(self, unit_builder: UnitBuilder) -> None:
        self._unit_builder = unit_builder

    def build_reinforcements(
        self,
        scenario: Scenario,
        faction_by_id: dict[str, Faction],
        player_by_faction_id: dict[str, Player],
    ) -> list[ReinforcementGroup]:
        """Convert scenario reinforcement definitions into runtime groups."""
        reinforcement_data = self._get_reinforcement_data(scenario)
        unit_by_id = {unit.id: unit for unit in scenario.units}
        return [
            self._build_group(
                group,
                unit_by_id,
                faction_by_id,
                player_by_faction_id,
            )
            for group in reinforcement_data
        ]

    def _get_reinforcement_data(self, scenario: Scenario) -> tuple | list:
        groups = getattr(scenario, "reinforcements", ())
        return groups if isinstance(groups, (list, tuple)) else ()

    def _build_group(
        self,
        group,
        unit_by_id: dict[str, ScenarioUnit],
        faction_by_id: dict[str, Faction],
        player_by_faction_id: dict[str, Player],
    ) -> ReinforcementGroup:
        return ReinforcementGroup(
            id=group.id,
            units=self._build_group_units(
                group.units,
                unit_by_id,
                faction_by_id,
                player_by_faction_id,
            ),
            arrival_turn=group.arrival_turn,
            coords=group.entry_location.coords,
        )

    def _build_group_units(
        self,
        unit_ids: tuple[str, ...],
        unit_by_id: dict[str, ScenarioUnit],
        faction_by_id: dict[str, Faction],
        player_by_faction_id: dict[str, Player],
    ) -> tuple[Unit, ...]:
        return tuple(
            self._build_reinforcement_unit(
                unit_by_id[unit_id],
                faction_by_id,
                player_by_faction_id,
            )
            for unit_id in unit_ids
        )

    def _build_reinforcement_unit(
        self,
        unit_data: ScenarioUnit,
        faction_by_id: dict[str, Faction],
        player_by_faction_id: dict[str, Player],
    ) -> Unit:
        faction_id = unit_data.faction
        unit = self._unit_builder(
            unit_data,
            faction_by_id[faction_id],
            player_by_faction_id[faction_id],
        )
        unit.mark_as_newly_deployed()
        return unit
