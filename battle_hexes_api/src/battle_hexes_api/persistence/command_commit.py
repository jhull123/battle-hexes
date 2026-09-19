"""Construction and submission of atomic persistence candidates."""

from .command_errors import CommandErrorTranslator
from .contracts import CommandReceipt, StoredGame
from .errors import (
    GameAlreadyExistsError,
    GameNotFoundError,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceCapacityError,
    PersistenceUnavailableError,
)


class CommandCandidateBuilder:
    """Build the complete game and receipt pair required for one commit."""

    def __init__(
        self,
        codec,
        clock,
        response_finalizer,
        game_expiry_seconds,
        receipt_expiry_seconds,
    ):
        self._codec = codec
        self._clock = clock
        self._response_finalizer = response_finalizer
        self._game_expiry_seconds = game_expiry_seconds
        self._receipt_expiry_seconds = receipt_expiry_seconds

    def build(
        self,
        *,
        identity,
        game,
        game_id,
        version,
        scenario_id,
        scenario_version,
        operation_result,
        serialize_response,
    ):
        """Encode game state and response with one timestamp."""
        now = self._commit_time()
        state = self._codec.encode(game, scenario_version=scenario_version)
        response = self._response_finalizer.finalize(
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

    def _commit_time(self):
        now = self._clock.now()
        if isinstance(now, bool) or not isinstance(now, int) or now < 0:
            raise ValueError("clock must return a non-negative integer epoch")
        return now


class CommandCommitter:
    """Submit candidates and centralize known versus ambiguous outcomes."""

    _RECONCILE_ERRORS = (
        GameAlreadyExistsError,
        GameVersionConflictError,
        PersistenceUnavailableError,
    )

    def __init__(self, repository, reconciler):
        self._repository = repository
        self._reconciler = reconciler

    def create(self, candidate, identity, game_id):
        return self._commit(
            lambda: self._repository.create_game(*candidate),
            lambda: self._reconciler.reconcile_creation(identity),
            game_id,
            translated_errors=(
                IdempotencyConflictError,
                PersistenceCapacityError,
            ),
        )

    def execute(self, candidate, identity, game_id, expected):
        return self._commit(
            lambda: self._repository.commit_command(expected, *candidate),
            lambda: self._reconciler.reconcile_execution(
                identity, game_id, expected
            ),
            game_id,
            expected,
            (
                IdempotencyConflictError,
                PersistenceCapacityError,
                GameNotFoundError,
            ),
        )

    @classmethod
    def _commit(
        cls,
        commit,
        reconcile,
        game_id,
        expected=None,
        translated_errors=(),
    ):
        try:
            return commit()
        except cls._RECONCILE_ERRORS:
            return reconcile()
        except translated_errors as error:
            raise CommandErrorTranslator.translate(
                error, game_id=game_id, expected=expected
            ) from None
        except Exception:
            return reconcile()
