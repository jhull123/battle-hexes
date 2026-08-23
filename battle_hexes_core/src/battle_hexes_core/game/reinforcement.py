"""Runtime state for a pending reinforcement group."""

from dataclasses import dataclass

from battle_hexes_core.unit.unit import Unit


@dataclass
class ReinforcementGroup:
    """Units waiting to enter atomically at a fixed location."""

    id: str
    units: tuple[Unit, ...]
    arrival_turn: int
    coords: tuple[int, int]
    entered: bool = False

    @property
    def player(self):
        """Return the common owner guaranteed by scenario validation."""
        return self.units[0].player
