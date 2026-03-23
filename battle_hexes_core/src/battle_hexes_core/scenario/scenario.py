"""Core dataclasses that describe a scenario definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from battle_hexes_core.game.objective import Objective


@dataclass(frozen=True)
class ScenarioFaction:
    """Representation of a faction as defined in a scenario."""

    id: str
    name: str
    color: str
    player: str


@dataclass(frozen=True)
class ScenarioUnit:
    """Representation of a unit as defined in a scenario."""

    id: str
    name: str
    faction: str
    type: str
    attack: int
    defense: int
    movement: int
    echelon: str | None = None
    defensive_fire_modifier: float = 1.0


@dataclass(frozen=True)
class ScenarioHexData:
    """
    Sparse description of hexes, such as terrain type and occupying units.
    """

    coords: tuple[int, int]
    terrain: str | None = None
    units: Tuple[str, ...] | None = None
    objectives: tuple[Objective, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScenarioTerrainType:
    """Representation of a terrain type as defined in a scenario."""

    color: str
    move_cost: int = 1
    defensive_fire_modifier: float = 1.0


@dataclass(frozen=True)
class ScenarioRoadType:
    """Representation of a road type as defined in a scenario."""

    edge_move_cost: float


@dataclass(frozen=True)
class ScenarioRoad:
    """Representation of a road path as defined in a scenario."""

    type: str
    path: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class ScenarioVictory:
    """Victory metadata defined for a scenario."""

    method: str
    scoring_side: str
    description: str | None = None


@dataclass(frozen=True)
class DefensiveFireConfig:
    base_probability: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class Scenario:
    """Container for the data required to configure a game scenario."""

    id: str
    name: str
    description: str | None = None
    victory: ScenarioVictory | None = None
    turn_limit: int | None = None
    board_size: Tuple[int, int] | None = None
    factions: tuple[ScenarioFaction, ...] = field(default_factory=tuple)
    units: tuple[ScenarioUnit, ...] = field(default_factory=tuple)
    terrain_default: str | None = None
    terrain_types: dict[str, ScenarioTerrainType] = field(default_factory=dict)
    road_types: dict[str, ScenarioRoadType] = field(default_factory=dict)
    roads: tuple[ScenarioRoad, ...] = field(default_factory=tuple)
    hex_data: tuple[ScenarioHexData, ...] = field(default_factory=tuple)
    defensive_fire: DefensiveFireConfig | None = None
