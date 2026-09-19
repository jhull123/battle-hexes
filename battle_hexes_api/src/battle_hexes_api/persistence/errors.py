"""Storage-neutral failures exposed by the persistence boundary."""


class PersistenceError(Exception):
    """Base class for persistence failures safe for API consumers."""


class GameNotFoundError(PersistenceError):
    """The requested game does not exist or has logically expired."""


class GameAlreadyExistsError(PersistenceError):
    """An unexpired game already uses the requested identifier."""


class GameVersionConflictError(PersistenceError):
    """The persisted version does not match the caller's expectation."""

    def __init__(self, expected_version, current_version=None):
        self.expected_version = expected_version
        self.current_version = current_version
        super().__init__(expected_version, current_version)


class IdempotencyConflictError(PersistenceError):
    """An idempotency digest already belongs to a different command."""


class SavedGameIncompatibleError(PersistenceError):
    """A saved state or scenario version cannot be loaded."""


class PersistenceCapacityError(PersistenceError):
    """A complete encoded persistence item exceeds the safe budget."""

    def __init__(self, item_kind, measured_bytes, limit_bytes):
        self.item_kind = item_kind
        self.measured_bytes = measured_bytes
        self.limit_bytes = limit_bytes
        super().__init__(item_kind, measured_bytes, limit_bytes)


class PersistenceUnavailableError(PersistenceError):
    """Storage is unavailable or the result of a commit is ambiguous."""
