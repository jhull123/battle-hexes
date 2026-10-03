"""Provider-independent persistence values and interfaces."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol

from .errors import PersistenceCapacityError


def _require_nonempty_string(name, value):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _require_positive_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _require_epoch(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer epoch")


def _require_digest(name, value):
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class CommandIdentity:
    """Digested identifiers for a command; never contains the raw key."""

    key_digest: str
    request_fingerprint: str

    def __post_init__(self):
        _require_digest("key_digest", self.key_digest)
        _require_digest("request_fingerprint", self.request_fingerprint)


@dataclass(frozen=True)
class StoredGame:
    """One encoded, versioned game snapshot."""

    game_id: str
    version: int
    state_schema_version: int
    scenario_id: str
    scenario_version: str
    state: bytes
    updated_at: int
    expires_at: int

    def __post_init__(self):
        _require_nonempty_string("game_id", self.game_id)
        _require_positive_integer("version", self.version)
        _require_positive_integer(
            "state_schema_version", self.state_schema_version
        )
        _require_nonempty_string("scenario_id", self.scenario_id)
        _require_nonempty_string("scenario_version", self.scenario_version)
        if not isinstance(self.state, bytes):
            raise ValueError("state must be bytes")
        try:
            self.state.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("state must contain UTF-8") from error
        _require_epoch("updated_at", self.updated_at)
        _require_epoch("expires_at", self.expires_at)
        if self.expires_at <= self.updated_at:
            raise ValueError("expires_at must be later than updated_at")


@dataclass(frozen=True)
class CommandReceipt:
    """An immutable, exactly replayable successful command response."""

    identity: CommandIdentity
    game_id: str
    game_version: int
    status_code: int
    content_type: str
    response_body: bytes
    response_headers: Mapping[str, str]
    created_at: int
    expires_at: int

    def __post_init__(self):
        if not isinstance(self.identity, CommandIdentity):
            raise ValueError("identity must be a CommandIdentity")
        _require_nonempty_string("game_id", self.game_id)
        _require_positive_integer("game_version", self.game_version)
        if (
            isinstance(self.status_code, bool)
            or not isinstance(self.status_code, int)
            or not 100 <= self.status_code <= 599
        ):
            raise ValueError("status_code must be an HTTP status code")
        _require_nonempty_string("content_type", self.content_type)
        if not isinstance(self.response_body, bytes):
            raise ValueError("response_body must be bytes")
        if not isinstance(self.response_headers, Mapping):
            raise ValueError("response_headers must be a mapping")
        headers = dict(self.response_headers)
        if any(
            not isinstance(name, str)
            or not name
            or not isinstance(value, str)
            for name, value in headers.items()
        ):
            raise ValueError(
                "response header names and values must be strings"
            )
        object.__setattr__(self, "response_headers", MappingProxyType(headers))
        _require_epoch("created_at", self.created_at)
        _require_epoch("expires_at", self.expires_at)
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be later than created_at")


class GameRepository(Protocol):
    """Atomic persistence operations required by command orchestration."""

    def load_game(self, game_id: str) -> StoredGame:
        ...

    def find_receipt(self, key_digest: str) -> CommandReceipt | None:
        ...

    def create_game(
        self, game: StoredGame, receipt: CommandReceipt
    ) -> CommandReceipt:
        ...

    def commit_command(
        self,
        expected_version: int,
        game: StoredGame,
        receipt: CommandReceipt,
    ) -> CommandReceipt:
        ...


class Clock(Protocol):
    """Source of integral Unix epoch seconds."""

    def now(self) -> int:
        ...


class EncodedItemSizer(Protocol):
    """Adapter-specific measurement of one complete encoded item."""

    def size_bytes(self, item: Mapping[str, object]) -> int:
        ...


@dataclass(frozen=True)
class EncodedItemBudget:
    """Shared inclusive safe-size policy for complete encoded items."""

    limit_bytes: int = 350 * 1024

    def __post_init__(self):
        _require_positive_integer("limit_bytes", self.limit_bytes)

    def require_fits(self, item_kind, encoded_size_bytes):
        _require_nonempty_string("item_kind", item_kind)
        if (
            isinstance(encoded_size_bytes, bool)
            or not isinstance(encoded_size_bytes, int)
            or encoded_size_bytes < 0
        ):
            raise ValueError(
                "encoded_size_bytes must be a non-negative integer"
            )
        if encoded_size_bytes > self.limit_bytes:
            raise PersistenceCapacityError(
                item_kind, encoded_size_bytes, self.limit_bytes
            )
