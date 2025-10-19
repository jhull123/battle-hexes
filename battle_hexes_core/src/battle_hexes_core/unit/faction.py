"""Core representation of a faction within the game."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False, slots=True)
class Faction:
    """Lightweight data container describing a faction."""

    id: str
    name: str
    color: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Faction) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
