"""Immutable history records for resolved normal combat."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CombatUnitSnapshot:
    """The public values a unit had when it participated in combat."""

    name: str
    attack: int
    defense: int
    movement: int


@dataclass(frozen=True)
class CombatTerrainSnapshot:
    """The defender terrain modifier selected by the combat rule."""

    name: str
    odds_shift: int


@dataclass(frozen=True)
class CombatOutcomeSnapshot:
    """The CRT result and a readable account of its actual effects."""

    code: str
    text: str
    summary: str


@dataclass(frozen=True)
class CombatEvent:
    """Complete, immutable history of one normal combat resolution."""

    turn_number: int
    player_name: str
    attackers: tuple[CombatUnitSnapshot, ...]
    defenders: tuple[CombatUnitSnapshot, ...]
    base_odds: tuple[int, int]
    modified_odds: tuple[int, int]
    defender_terrain: CombatTerrainSnapshot
    die_roll: int
    result: CombatOutcomeSnapshot
    eliminated_units: tuple[str, ...]
    retreated_units: tuple[str, ...]
