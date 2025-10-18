"""Core dataclasses that describe a scenario definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


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
    starting_coords: Tuple[int, int]


@dataclass(frozen=True)
class Scenario:
    """Container for the data required to configure a game scenario."""

    id: str
    name: str
    description: str | None = None
    board_size: Tuple[int, int] | None = None
    factions: tuple[ScenarioFaction, ...] = field(default_factory=tuple)
    units: tuple[ScenarioUnit, ...] = field(default_factory=tuple)
