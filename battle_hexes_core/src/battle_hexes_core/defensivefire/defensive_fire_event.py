"""Immutable history records for resolved defensive-fire shots."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DefensiveFireUnitSnapshot:
    unit_id: str
    name: str


@dataclass(frozen=True)
class DefensiveFireEvent:
    turn_number: int
    player_name: str
    firing_unit: DefensiveFireUnitSnapshot
    target_unit: DefensiveFireUnitSnapshot
    success_probability: float
    random_roll: float
    outcome: str
    summary: str
