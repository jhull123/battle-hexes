"""Storage-independent orchestration for authoritative game commands."""

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .contracts import CommandReceipt, StoredGame
from .errors import (
    GameAlreadyExistsError,
    GameNotFoundError,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceCapacityError,
    PersistenceUnavailableError,
    SavedGameIncompatibleError,
)
from .identity import create_command_identity


_ONE_DAY_SECONDS = 24 * 60 * 60
_TRANSPORT_HEADERS = frozenset({"content-length", "date", "server"})


def _positive_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _copy_mapping(value, description):
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
            _copy_mapping(self.validated_body, "validated_body"),
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
            self, "headers", _copy_mapping(self.headers, "headers")
        )


@dataclass(frozen=True)
class CreatedGame:
    """A new game and the immutable scenario metadata needed to save it."""

    game: object
    scenario_id: str
    scenario_version: str


class CommandServiceError(Exception):
    """Framework-neutral, client-safe command failure."""

    def __init__(
        self,
        status_code,
        code,
        message,
        *,
        game_id=None,
        expected_game_version=None,
        current_game_version=None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.game_id = game_id
        self.expected_game_version = expected_game_version
        self.current_game_version = current_game_version
        super().__init__(code)

    def as_dict(self):
        """Return the camel-case API error body without absent fields."""
        result = {"code": self.code, "message": self.message}
        optional = (
            ("gameId", self.game_id),
            ("expectedGameVersion", self.expected_game_version),
            ("currentGameVersion", self.current_game_version),
        )
        result.update(
            (name, value) for name, value in optional if value is not None
        )
        return result


class GameCommandService:
    """Execute, persist, and replay one authoritative game command."""

    def __init__(
        self,
        repository,
        codec,
        clock,
        game_expiry_seconds=_ONE_DAY_SECONDS,
        receipt_expiry_seconds=_ONE_DAY_SECONDS,
    ):
        if not _positive_integer(game_expiry_seconds):
            raise ValueError("game_expiry_seconds must be a positive integer")
        if not _positive_integer(receipt_expiry_seconds):
            raise ValueError(
                "receipt_expiry_seconds must be a positive integer"
            )
        self._repository = repository
        self._codec = codec
        self._clock = clock
        self._game_expiry_seconds = game_expiry_seconds
        self._receipt_expiry_seconds = receipt_expiry_seconds

    def create(self, request, create_game, serialize_response):
        """Create version one and atomically store its successful response."""
        identity = self._identity(request, creation=True)
        replay = self._find_initial_receipt(identity)
        if replay is not None:
            return self._response_from_receipt(replay)

        created = self._created_game(create_game())
        game_id = self._game_id(created.game)
        now = self._commit_time()
        try:
            state = self._codec.encode(
                created.game, scenario_version=created.scenario_version
            )
        except SavedGameIncompatibleError as error:
            raise self._translated(error, game_id=game_id) from None
        candidate = self._candidate(
            identity=identity,
            game=created.game,
            game_id=game_id,
            version=1,
            scenario_id=created.scenario_id,
            scenario_version=created.scenario_version,
            state=state,
            operation_result=None,
            serialize_response=serialize_response,
            now=now,
        )
        try:
            receipt = self._repository.create_game(*candidate)
        except (GameAlreadyExistsError, GameVersionConflictError,
                PersistenceUnavailableError):
            receipt = self._reconcile_creation(identity)
        except (IdempotencyConflictError, PersistenceCapacityError) as error:
            raise self._translated(error, game_id=game_id) from None
        except Exception:
            receipt = self._reconcile_creation(identity)
        return self._response_from_authoritative(receipt, identity)

    def execute(self, game_id, request, apply_command, serialize_response):
        """Apply a command to a detached snapshot and atomically save N+1."""
        identity = self._identity(request, creation=False)
        replay = self._find_initial_receipt(identity)
        if replay is not None:
            return self._response_from_receipt(replay)

        stored = self._load_game(game_id)
        expected = request.expected_game_version
        try:
            game = self._codec.decode(stored)
        except SavedGameIncompatibleError as error:
            raise self._translated(error, game_id=game_id) from None
        if stored.version != expected:
            raise self._version_conflict(game_id, expected, stored.version)
        operation_result = apply_command(game)
        resulting_version = stored.version + 1
        now = self._commit_time()
        try:
            state = self._codec.encode(
                game, scenario_version=stored.scenario_version
            )
        except SavedGameIncompatibleError as error:
            raise self._translated(error, game_id=game_id) from None
        candidate = self._candidate(
            identity=identity,
            game=game,
            game_id=stored.game_id,
            version=resulting_version,
            scenario_id=stored.scenario_id,
            scenario_version=stored.scenario_version,
            state=state,
            operation_result=operation_result,
            serialize_response=serialize_response,
            now=now,
        )
        try:
            receipt = self._repository.commit_command(expected, *candidate)
        except (GameAlreadyExistsError, GameVersionConflictError,
                PersistenceUnavailableError):
            receipt = self._reconcile_execution(identity, game_id, expected)
        except (IdempotencyConflictError, PersistenceCapacityError,
                GameNotFoundError) as error:
            raise self._translated(
                error, game_id=game_id, expected=expected
            ) from None
        except Exception:
            receipt = self._reconcile_execution(identity, game_id, expected)
        return self._response_from_authoritative(receipt, identity)

    def _identity(self, request, creation):
        if not isinstance(request, CommandRequest):
            raise self._error(400, "invalidIdempotencyKey")
        expected = request.expected_game_version
        if creation:
            if expected is not None:
                raise self._error(400, "invalidExpectedGameVersion")
        elif expected is None:
            raise self._error(428, "expectedGameVersionRequired")
        elif not _positive_integer(expected):
            raise self._error(400, "invalidExpectedGameVersion")
        try:
            return create_command_identity(
                request.idempotency_key,
                request.method,
                request.normalized_route,
                expected,
                dict(request.validated_body),
            )
        except ValueError as error:
            code = (
                "invalidExpectedGameVersion"
                if "expected_version" in str(error)
                else "invalidIdempotencyKey"
            )
            raise self._error(400, code) from None

    def _find_initial_receipt(self, identity):
        try:
            receipt = self._repository.find_receipt(identity.key_digest)
        except Exception as error:
            raise self._translated_read(error) from None
        if receipt is None:
            return None
        self._require_matching_receipt(receipt, identity)
        return receipt

    def _load_game(self, game_id):
        try:
            return self._repository.load_game(game_id)
        except Exception as error:
            raise self._translated_read(error, game_id=game_id) from None

    def _candidate(
        self, *, identity, game, game_id, version, scenario_id,
        scenario_version, state, operation_result, serialize_response, now
    ):
        response = self._finalize_response(
            serialize_response(game, operation_result, version), version
        )
        stored = StoredGame(
            game_id=game_id,
            version=version,
            state_schema_version=self._codec.STATE_SCHEMA_VERSION,
            scenario_id=scenario_id,
            scenario_version=scenario_version,
            state=state,
            updated_at=now,
            expires_at=now + self._game_expiry_seconds,
        )
        receipt = CommandReceipt(
            identity=identity,
            game_id=game_id,
            game_version=version,
            status_code=response.status_code,
            content_type=response.content_type,
            response_body=response.body,
            response_headers=response.headers,
            created_at=now,
            expires_at=now + self._receipt_expiry_seconds,
        )
        return stored, receipt

    @staticmethod
    def _created_game(value):
        if isinstance(value, CreatedGame):
            created = value
        elif isinstance(value, tuple) and len(value) == 3:
            created = CreatedGame(*value)
        elif isinstance(value, tuple) and len(value) == 2:
            game, scenario_version = value
            created = CreatedGame(game, getattr(game, "scenario_id", None),
                                  scenario_version)
        else:
            try:
                created = CreatedGame(
                    value.game, value.scenario_id, value.scenario_version
                )
            except AttributeError as error:
                raise ValueError(
                    "create_game must return game and scenario metadata"
                ) from error
        if not isinstance(created.scenario_id, str) or not created.scenario_id:
            raise ValueError("scenario_id must be a non-empty string")
        if (
            not isinstance(created.scenario_version, str)
            or not created.scenario_version
        ):
            raise ValueError("scenario_version must be a non-empty string")
        return created

    @staticmethod
    def _game_id(game):
        value = game.get_id() if hasattr(game, "get_id") else game.id
        game_id = str(value)
        if not game_id:
            raise ValueError("game ID must not be empty")
        return game_id

    def _commit_time(self):
        now = self._clock.now()
        if isinstance(now, bool) or not isinstance(now, int) or now < 0:
            raise ValueError("clock must return a non-negative integer epoch")
        return now

    @classmethod
    def _finalize_response(cls, value, version):
        if isinstance(value, SuccessfulResponse):
            if value.game_version != version:
                raise ValueError(
                    "serialized response has the wrong game version"
                )
            status, body, content_type, headers = (
                value.status_code,
                value.body,
                value.content_type,
                value.headers,
            )
        elif isinstance(value, tuple) and len(value) == 4:
            status, body, content_type, headers = value
        else:
            try:
                status = value.status_code
                body = value.body
                content_type = value.content_type
                headers = value.headers
            except AttributeError as error:
                raise ValueError(
                    "serializer returned an invalid response"
                ) from error
        if (
            isinstance(status, bool)
            or not isinstance(status, int)
            or not 200 <= status <= 299
        ):
            raise ValueError("successful status_code must be in the 2xx range")
        if not isinstance(body, bytes):
            raise ValueError("serialized response body must be bytes")
        if not isinstance(content_type, str) or not content_type:
            raise ValueError("content_type must be a non-empty string")
        canonical = cls._canonical_headers(headers, content_type, version)
        return SuccessfulResponse(
            status, body, content_type, canonical, version
        )

    @staticmethod
    def _canonical_headers(headers, content_type, version):
        if not isinstance(headers, Mapping):
            raise ValueError("response headers must be a mapping")
        canonical = {}
        seen = set()
        for name, value in headers.items():
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(value, str)
            ):
                raise ValueError("response headers must contain strings")
            lowered = name.lower()
            if lowered in seen:
                raise ValueError("response header names must be unique")
            seen.add(lowered)
            if lowered in _TRANSPORT_HEADERS or lowered == "content-type":
                continue
            canonical_name = "-".join(
                part.capitalize() for part in lowered.split("-")
            )
            canonical[canonical_name] = value
        expected = str(version)
        supplied = canonical.get("Game-Version")
        if supplied is not None and supplied != expected:
            raise ValueError("Game-Version does not match resulting version")
        canonical["Game-Version"] = expected
        return canonical

    def _reconcile_creation(self, identity):
        receipt = self._reconciliation_receipt(identity)
        if receipt is None:
            raise self._error(503, "gamePersistenceUnavailable")
        return receipt

    def _reconcile_execution(self, identity, game_id, expected):
        receipt = self._reconciliation_receipt(identity)
        if receipt is not None:
            return receipt
        try:
            stored = self._repository.load_game(game_id)
        except GameNotFoundError:
            raise self._error(404, "gameNotFound", game_id=game_id) from None
        except Exception:
            raise self._error(503, "gamePersistenceUnavailable") from None
        if stored.version != expected:
            raise self._version_conflict(game_id, expected, stored.version)
        raise self._error(503, "gamePersistenceUnavailable")

    def _reconciliation_receipt(self, identity):
        try:
            receipt = self._repository.find_receipt(identity.key_digest)
        except Exception:
            raise self._error(503, "gamePersistenceUnavailable") from None
        if receipt is not None:
            self._require_matching_receipt(receipt, identity)
        return receipt

    @staticmethod
    def _require_matching_receipt(receipt, identity):
        if receipt.identity.key_digest != identity.key_digest:
            raise GameCommandService._error(503, "gamePersistenceUnavailable")
        if (
            receipt.identity.request_fingerprint
            != identity.request_fingerprint
        ):
            raise GameCommandService._error(409, "idempotencyKeyReused")

    @staticmethod
    def _response_from_receipt(receipt):
        return SuccessfulResponse(
            receipt.status_code,
            receipt.response_body,
            receipt.content_type,
            receipt.response_headers,
            receipt.game_version,
        )

    def _response_from_authoritative(self, receipt, identity):
        if not isinstance(receipt, CommandReceipt):
            raise self._error(503, "gamePersistenceUnavailable")
        self._require_matching_receipt(receipt, identity)
        return self._response_from_receipt(receipt)

    @classmethod
    def _translated_read(cls, error, game_id=None):
        if isinstance(error, (GameNotFoundError, SavedGameIncompatibleError)):
            return cls._translated(error, game_id=game_id)
        return cls._error(503, "gamePersistenceUnavailable")

    @classmethod
    def _translated(cls, error, game_id=None, expected=None):
        if isinstance(error, IdempotencyConflictError):
            return cls._error(409, "idempotencyKeyReused")
        if isinstance(error, GameNotFoundError):
            return cls._error(404, "gameNotFound", game_id=game_id)
        if isinstance(error, GameVersionConflictError):
            return cls._version_conflict(
                game_id,
                error.expected_version
                if error.expected_version is not None
                else expected,
                error.current_version,
            )
        if isinstance(error, SavedGameIncompatibleError):
            return cls._error(409, "savedGameIncompatible", game_id=game_id)
        if isinstance(error, PersistenceCapacityError):
            return cls._error(
                507, "gamePersistenceCapacityExceeded", game_id=game_id
            )
        return cls._error(503, "gamePersistenceUnavailable")

    @classmethod
    def _version_conflict(cls, game_id, expected, current):
        return cls._error(
            409,
            "gameVersionConflict",
            game_id=game_id,
            expected_game_version=expected,
            current_game_version=current,
        )

    @staticmethod
    def _error(status, code, **details):
        messages = {
            "invalidIdempotencyKey": "The idempotency key is invalid.",
            "invalidExpectedGameVersion": (
                "The expected game version is invalid."
            ),
            "expectedGameVersionRequired": (
                "An expected game version is required."
            ),
            "idempotencyKeyReused": (
                "The idempotency key was reused for another command."
            ),
            "gameNotFound": "The game was not found.",
            "gameVersionConflict": "The game version has changed.",
            "savedGameIncompatible": "The saved game is incompatible.",
            "gamePersistenceCapacityExceeded": (
                "The game is too large to persist."
            ),
            "gamePersistenceUnavailable": "Game persistence is unavailable.",
        }
        return CommandServiceError(status, code, messages[code], **details)
