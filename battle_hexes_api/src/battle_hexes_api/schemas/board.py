"""Board-related Pydantic schemas used by the API."""

from typing import List

from pydantic import BaseModel

from .unit import UnitModel


class BoardModel(BaseModel):
    """Serialized representation of the in-memory board."""

    rows: int
    columns: int
    units: List[UnitModel]
