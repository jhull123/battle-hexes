from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DefensiveFireSettings:
    base_probability: float = 0.0
    minimum: float = 0.0
    maximum: float = 1.0


@dataclass(frozen=True)
class DefensiveFireResult:
    firing_unit_id: str
    target_unit_id: str
    trigger_hex: tuple[int, int]
    target_hex_before: tuple[int, int]
    outcome: str
    retreat_destination: tuple[int, int] | None
    spent_defensive_fire: bool = True
    probability: float | None = None
    roll: float | None = None


@dataclass
class MovementResolutionResult:
    defensive_fire_results: list[DefensiveFireResult] = field(
        default_factory=list
    )
