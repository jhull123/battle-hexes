"""Best-effort, payload-free telemetry for repository operations."""

from dataclasses import asdict, dataclass
import json
import logging
import sys
from time import perf_counter

from .errors import (
    GameAlreadyExistsError,
    GameNotFoundError,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceCapacityError,
    PersistenceUnavailableError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepositoryOperationEvent:
    repository: str
    operation: str
    outcome: str
    latency_ms: float
    game_version: int | None = None
    game_item_bytes: int | None = None
    receipt_item_bytes: int | None = None
    dynamodb_error_category: str | None = None

    def fields(self):
        """Return only applicable fields for structured sinks."""
        return {
            key: value for key, value in asdict(self).items()
            if value is not None
        }


class LoggingTelemetrySink:
    """Emit a bounded JSON event suitable for log metrics and queries."""

    def __init__(self):
        if not logger.handlers:
            handler = logging.StreamHandler(sys.__stderr__ or sys.stderr)
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.propagate = False
        logger.setLevel(logging.INFO)

    def emit(self, event):
        logger.info(
            "repository_operation_completed %s",
            json.dumps(event.fields(), sort_keys=True, separators=(",", ":")),
        )


class InstrumentedGameRepository:
    """Decorate a repository without allowing telemetry to affect results."""

    def __init__(
        self, repository, implementation, item_sizer, game_encoder,
        receipt_encoder, sink=None, timer=perf_counter,
    ):
        self._repository = repository
        self._implementation = implementation
        self._item_sizer = item_sizer
        self._game_encoder = game_encoder
        self._receipt_encoder = receipt_encoder
        self._sink = sink or LoggingTelemetrySink()
        self._timer = timer

    def load_game(self, game_id):
        return self._run("load_game", self._repository.load_game, game_id)

    def find_receipt(self, key_digest):
        return self._run(
            "find_receipt", self._repository.find_receipt, key_digest
        )

    def create_game(self, game, receipt):
        return self._run(
            "create_game", self._repository.create_game, game, receipt,
            game=game, receipt=receipt,
        )

    def commit_command(self, expected_version, game, receipt):
        return self._run(
            "commit_command", self._repository.commit_command,
            expected_version, game, receipt, game=game, receipt=receipt,
        )

    def _run(self, operation, callback, *args, game=None, receipt=None):
        started = self._timer()
        outcome = "success"
        error_category = None
        result = None
        try:
            result = callback(*args)
            if operation == "find_receipt":
                outcome = "replay" if result is not None \
                    else "not_found_expired"
            return result
        except Exception as error:
            outcome = _outcome(error)
            error_category = getattr(error, "dynamodb_error_category", None)
            raise
        finally:
            event = self._event(
                operation, outcome, started, game, receipt, result,
                error_category,
            )
            try:
                self._sink.emit(event)
            except Exception:
                # Observability is deliberately outside the correctness path.
                pass

    def _event(
        self, operation, outcome, started, game, receipt, result,
        error_category,
    ):
        game_size = self._safe_size(self._game_encoder, game)
        receipt_size = self._safe_size(self._receipt_encoder, receipt)
        version = getattr(game, "version", None)
        if version is None:
            version = getattr(result, "version", None)
        if version is None:
            version = getattr(result, "game_version", None)
        return RepositoryOperationEvent(
            repository=self._implementation,
            operation=operation,
            outcome=outcome,
            latency_ms=max(0.0, (self._timer() - started) * 1000),
            game_version=version,
            game_item_bytes=game_size,
            receipt_item_bytes=receipt_size,
            dynamodb_error_category=error_category,
        )

    def _safe_size(self, encoder, value):
        if value is None:
            return None
        try:
            return self._item_sizer.size_bytes(encoder(value))
        except Exception:
            return None


def _outcome(error):
    if isinstance(error, GameVersionConflictError):
        return "version_conflict"
    if isinstance(error, IdempotencyConflictError):
        return "idempotency_conflict"
    if isinstance(error, GameNotFoundError):
        return "not_found_expired"
    if isinstance(error, PersistenceCapacityError):
        return "capacity_exceeded"
    if isinstance(error, PersistenceUnavailableError):
        return "persistence_unavailable"
    if isinstance(error, GameAlreadyExistsError):
        return "already_exists"
    return "unknown_failure"
