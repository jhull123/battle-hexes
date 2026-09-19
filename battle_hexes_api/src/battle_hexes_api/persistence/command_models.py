"""Framework-neutral values used by the command service."""

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


def positive_integer(value):
    """Return whether *value* is a non-boolean positive integer."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def copy_mapping(value, description):
    """Defensively copy a mapping before exposing it from a value object."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{description} must be a mapping")
    return MappingProxyType(deepcopy(dict(value)))


@dataclass(frozen=True)
class CommandRequest:
    """Validated, framework-neutral input for one command."""

    idempotency_key: str
    method: str
    normalized_route: str
    validated_body: Mapping[str, object]
    expected_game_version: int | None

    def __post_init__(self):
        object.__setattr__(
            self,
            "validated_body",
            copy_mapping(self.validated_body, "validated_body"),
        )


@dataclass(frozen=True)
class SuccessfulResponse:
    """The exact application response produced by a committed command."""

    status_code: int
    body: bytes
    content_type: str
    headers: Mapping[str, str]
    game_version: int

    def __post_init__(self):
        if not isinstance(self.body, bytes):
            raise ValueError("body must be bytes")
        object.__setattr__(self, "body", memoryview(self.body).tobytes())
        object.__setattr__(
            self, "headers", copy_mapping(self.headers, "headers")
        )


@dataclass(frozen=True)
class CreatedGame:
    """A new game and the immutable scenario metadata needed to save it."""

    game: object
    scenario_id: str
    scenario_version: str
