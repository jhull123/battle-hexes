"""Relationship validation for scenario reinforcement definitions."""

from battle_hexes_core.scenario.scenario import Scenario


class ReinforcementsValidator:
    """Validate fixed reinforcement groups and their unit assignments."""

    def validate(self, scenario: Scenario) -> None:
        unit_by_id = {unit.id: unit for unit in scenario.units}
        faction_players = {
            faction.id: faction.player for faction in scenario.factions
        }
        assigned_units = self._initially_deployed_units(scenario)
        group_ids: set[str] = set()

        for group in scenario.reinforcements:
            self._validate_id(group.id, group_ids)
            if group.arrival_turn < 1:
                raise ValueError(
                    f"Reinforcement '{group.id}' arrival turn must be positive"
                )
            if group.entry_location.mode != "fixed":
                raise ValueError(
                    f"Reinforcement '{group.id}' entry mode must be fixed"
                )
            self._validate_coords(scenario, group.entry_location.coords)
            self._validate_units(
                group.id,
                group.units,
                unit_by_id,
                faction_players,
                assigned_units,
            )
            group_ids.add(group.id)
            assigned_units.update(group.units)

    def _initially_deployed_units(self, scenario: Scenario) -> set[str]:
        deployed: set[str] = set()
        for entry in scenario.hex_data:
            for unit_id in entry.units or ():
                if unit_id in deployed:
                    raise ValueError(
                        f"Unit '{unit_id}' has multiple deployment sources"
                    )
                deployed.add(unit_id)
        return deployed

    def _validate_id(self, group_id: str, seen: set[str]) -> None:
        if not group_id.strip():
            raise ValueError("Reinforcement id must not be empty")
        if group_id in seen:
            raise ValueError(f"Duplicate reinforcement id '{group_id}'")

    def _validate_coords(
        self,
        scenario: Scenario,
        coords: tuple[int, int],
    ) -> None:
        rows, columns = scenario.board_size
        row, column = coords
        if not (0 <= row < rows and 0 <= column < columns):
            raise ValueError(
                f"Reinforcement entry coords out of bounds: {coords}"
            )

    def _validate_units(
        self,
        group_id: str,
        unit_ids: tuple[str, ...],
        unit_by_id: dict,
        faction_players: dict[str, str],
        assigned_units: set[str],
    ) -> None:
        if not unit_ids:
            raise ValueError(
                f"Reinforcement '{group_id}' must contain at least one unit"
            )
        if len(set(unit_ids)) != len(unit_ids):
            raise ValueError(
                f"Reinforcement '{group_id}' repeats a unit id"
            )
        unknown = [
            unit_id for unit_id in unit_ids if unit_id not in unit_by_id
        ]
        if unknown:
            raise ValueError(f"Unknown reinforcement unit '{unknown[0]}'")
        reused = [unit_id for unit_id in unit_ids if unit_id in assigned_units]
        if reused:
            raise ValueError(
                f"Unit '{reused[0]}' has multiple deployment sources"
            )
        owners = {
            faction_players.get(unit_by_id[unit_id].faction)
            for unit_id in unit_ids
        }
        if len(owners) != 1 or None in owners:
            raise ValueError(
                f"Reinforcement '{group_id}' units must belong to one player"
            )
