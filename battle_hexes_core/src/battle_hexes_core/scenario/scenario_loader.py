"""Utilities for loading scenario definitions from JSON files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel, ConfigDict, ValidationError

from .scenario import (
    Scenario,
    ScenarioFaction,
    ScenarioHexData,
    ScenarioTerrainType,
    ScenarioUnit,
)


@dataclass(frozen=True)
class ScenarioPaths:
    """Resolved filesystem locations for scenario resources."""

    directory: Path

    @classmethod
    def default(cls) -> "ScenarioPaths":
        base_dir = Path(__file__).resolve().parents[1]
        return cls(directory=base_dir / "scenarios")


class ScenarioFactionData(BaseModel):
    """Faction configuration as defined in a scenario file."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    color: str
    player: str


class ScenarioUnitData(BaseModel):
    """Unit configuration as defined in a scenario file."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    faction: str
    type: str
    attack: int
    defense: int
    movement: int


class ScenarioTerrainTypeData(BaseModel):
    """Terrain type configuration as defined in a scenario file."""

    model_config = ConfigDict(frozen=True)

    color: str


class ScenarioHexDataEntry(BaseModel):
    """Hex configuration as defined in a scenario file."""

    model_config = ConfigDict(frozen=True)

    coords: tuple[int, int]
    terrain: str | None = None
    units: list[str] | None = None


class ScenarioData(BaseModel):
    """Full scenario definition parsed from a JSON file."""

    model_config = ConfigDict(frozen=True)

    version: str
    id: str
    name: str
    description: str
    board_size: tuple[int, int]
    factions: list[ScenarioFactionData]
    units: list[ScenarioUnitData]
    terrain_default: str | None = None
    terrain_types: dict[str, ScenarioTerrainTypeData] | None = None
    hex_data: list[ScenarioHexDataEntry] | None = None

    def to_core(self) -> Scenario:
        """Convert the validated payload into a core :class:`Scenario`."""

        return Scenario(
            id=self.id,
            name=self.name,
            description=self.description,
            board_size=self.board_size,
            factions=tuple(
                ScenarioFaction(
                    id=faction.id,
                    name=faction.name,
                    color=faction.color,
                    player=faction.player,
                )
                for faction in self.factions
            ),
            units=tuple(
                ScenarioUnit(
                    id=unit.id,
                    name=unit.name,
                    faction=unit.faction,
                    type=unit.type,
                    attack=unit.attack,
                    defense=unit.defense,
                    movement=unit.movement
                )
                for unit in self.units
            ),
            terrain_default=self.terrain_default,
            terrain_types=(
                {
                    key: ScenarioTerrainType(color=terrain_type.color)
                    for key, terrain_type in self.terrain_types.items()
                }
                if self.terrain_types
                else {}
            ),
            hex_data=(
                tuple(
                    ScenarioHexData(
                        terrain=entry.terrain,
                        units=tuple(entry.units) if entry.units else None,
                    )
                    for entry in self.hex_data
                )
                if self.hex_data
                else ()
            ),
        )


def _load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise FileNotFoundError(
            f"Scenario file '{path}' was not found"
        ) from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(
            f"Scenario file '{path}' contains invalid JSON"
        ) from exc


def load_scenario_data(
    scenario_id: str, *,
    scenario_dir: Path | None = None,
) -> ScenarioData:
    """Load the scenario definition for ``scenario_id``."""

    paths = (
        ScenarioPaths.default()
        if scenario_dir is None
        else ScenarioPaths(directory=Path(scenario_dir))
    )
    scenario_path = paths.directory / f"{scenario_id}.json"

    payload = _load_json(scenario_path)
    try:
        scenario = ScenarioData.model_validate(payload)
    except ValidationError as exc:  # pragma: no cover - defensive
        raise ValueError(
            "Scenario file "
            f"'{scenario_path}' is not a valid scenario definition"
        ) from exc

    if scenario.id != scenario_id:
        raise ValueError(
            f"Scenario '{scenario_id}' does not match file contents "
            f"(found id '{scenario.id}')"
        )

    return scenario


def load_scenario(
    scenario_id: str, *,
    scenario_dir: Path | None = None,
) -> Scenario:
    """Load ``scenario_id`` and return a core :class:`Scenario`."""

    scenario_data = load_scenario_data(
        scenario_id, scenario_dir=scenario_dir
    )
    return scenario_data.to_core()


def iter_scenario_data(
    *, scenario_dir: Path | None = None
) -> Iterator[ScenarioData]:
    """Yield :class:`ScenarioData` objects for all scenario files."""

    paths = (
        ScenarioPaths.default()
        if scenario_dir is None
        else ScenarioPaths(directory=Path(scenario_dir))
    )
    if not paths.directory.exists():  # pragma: no cover - defensive
        return

    for path in sorted(paths.directory.glob("*.json")):
        payload = _load_json(path)
        try:
            scenario = ScenarioData.model_validate(payload)
        except ValidationError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"Scenario file '{path}' is not a valid scenario definition"
            ) from exc
        yield scenario


def iter_scenarios(
    *, scenario_dir: Path | None = None
) -> Iterator[Scenario]:
    """Yield core :class:`Scenario` instances for all scenario files."""

    for scenario_data in iter_scenario_data(scenario_dir=scenario_dir):
        yield scenario_data.to_core()
