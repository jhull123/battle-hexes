"""Objective-related schema definitions."""

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.objective import Objective


class ObjectiveModel(BaseModel):
    """Serialized representation of a board objective."""

    row: int
    column: int
    points: int
    type: str

    @classmethod
    def from_objective(cls, objective: "Objective") -> "ObjectiveModel":
        """Create an ``ObjectiveModel`` from a core objective."""
        row, column = objective.coords
        return cls(
            row=row,
            column=column,
            points=objective.points,
            type=objective.type,
        )
