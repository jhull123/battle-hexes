"""Pydantic models for unit entities."""

from pydantic import BaseModel


class UnitModel(BaseModel):
    """Model representing a unit's complete state."""
    id: str
    name: str
    faction_id: str
    type: str
    attack: int
    defense: int
    move: int
    row: int
    column: int


class SparseUnit(BaseModel):
    """Model representing a unit's minimal state for position updates."""
    id: str
    row: int
    column: int
