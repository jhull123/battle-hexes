"""Definitions for the player types exposed by the public API."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerTypeDefinition:
    """Describe a player type option that can be selected on the frontend."""

    id: str
    name: str


SUPPORTED_PLAYER_TYPES: tuple[PlayerTypeDefinition, ...] = (
    PlayerTypeDefinition(id="human", name="Human"),
    PlayerTypeDefinition(id="random", name="Random Player"),
    PlayerTypeDefinition(id="q-learning", name="Q-Learning Player"),
)


def list_player_types() -> tuple[PlayerTypeDefinition, ...]:
    """Return the supported player type definitions."""

    return SUPPORTED_PLAYER_TYPES
