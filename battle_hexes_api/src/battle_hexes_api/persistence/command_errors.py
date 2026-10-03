"""Framework-neutral command-service errors and persistence translation."""

from .errors import (
    GameNotFoundError,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceCapacityError,
    SavedGameIncompatibleError,
)


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


class CommandErrorTranslator:
    """Build public errors without exposing storage implementation details."""

    _MESSAGES = {
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

    @classmethod
    def error(cls, status, code, **details):
        return CommandServiceError(
            status, code, cls._MESSAGES[code], **details
        )

    @classmethod
    def version_conflict(cls, game_id, expected, current):
        return cls.error(
            409,
            "gameVersionConflict",
            game_id=game_id,
            expected_game_version=expected,
            current_game_version=current,
        )

    @classmethod
    def translate_read(cls, error, game_id=None):
        if isinstance(error, (GameNotFoundError, SavedGameIncompatibleError)):
            return cls.translate(error, game_id=game_id)
        return cls.unavailable()

    @classmethod
    def translate(cls, error, game_id=None, expected=None):
        if isinstance(error, IdempotencyConflictError):
            return cls.error(409, "idempotencyKeyReused")
        if isinstance(error, GameNotFoundError):
            return cls.error(404, "gameNotFound", game_id=game_id)
        if isinstance(error, GameVersionConflictError):
            return cls.version_conflict(
                game_id,
                error.expected_version
                if error.expected_version is not None
                else expected,
                error.current_version,
            )
        if isinstance(error, SavedGameIncompatibleError):
            return cls.error(409, "savedGameIncompatible", game_id=game_id)
        if isinstance(error, PersistenceCapacityError):
            return cls.error(
                507, "gamePersistenceCapacityExceeded", game_id=game_id
            )
        return cls.unavailable()

    @classmethod
    def unavailable(cls):
        return cls.error(503, "gamePersistenceUnavailable")
