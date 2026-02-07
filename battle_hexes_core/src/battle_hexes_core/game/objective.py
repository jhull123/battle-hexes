from dataclasses import dataclass


@dataclass(frozen=True)
class Objective:
    """Representation of a hex objective."""

    coords: tuple[int, int]
    points: int
    type: str
