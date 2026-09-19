"""Storage-independent orchestration for authoritative game commands."""

from .command_commit import CommandCandidateBuilder, CommandCommitter
from .command_errors import CommandErrorTranslator
from .command_models import CommandRequest, CreatedGame, positive_integer
from .command_reconciliation import CommandReconciler
from .command_response import CommandResponseFinalizer
from .errors import SavedGameIncompatibleError
from .identity import create_command_identity


_ONE_DAY_SECONDS = 24 * 60 * 60


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
        self._validate_expiries(game_expiry_seconds, receipt_expiry_seconds)
        reconciler = CommandReconciler(repository)
        self._repository = repository
        self._codec = codec
        self._reconciler = reconciler
        self._candidate_builder = CommandCandidateBuilder(
            codec,
            clock,
            CommandResponseFinalizer(),
            game_expiry_seconds,
            receipt_expiry_seconds,
        )
        self._committer = CommandCommitter(repository, reconciler)

    def create(self, request, create_game, serialize_response):
        """Create version one and atomically store its successful response."""
        identity = self._identity(request, creation=True)
        replay = self._reconciler.find_initial_receipt(identity)
        if replay is not None:
            return self._reconciler.authoritative_response(replay, identity)

        created = self._created_game(create_game())
        game_id = self._game_id(created.game)
        candidate = self._build_candidate(
            identity=identity,
            game=created.game,
            game_id=game_id,
            version=1,
            scenario_id=created.scenario_id,
            scenario_version=created.scenario_version,
            operation_result=None,
            serialize_response=serialize_response,
        )
        receipt = self._committer.create(candidate, identity, game_id)
        return self._reconciler.authoritative_response(receipt, identity)

    def execute(self, game_id, request, apply_command, serialize_response):
        """Apply a command to a detached snapshot and atomically save N+1."""
        identity = self._identity(request, creation=False)
        replay = self._reconciler.find_initial_receipt(identity)
        if replay is not None:
            return self._reconciler.authoritative_response(replay, identity)

        stored = self._load_game(game_id)
        expected = request.expected_game_version
        game = self._decode_game(stored, game_id)
        if stored.version != expected:
            raise CommandErrorTranslator.version_conflict(
                game_id, expected, stored.version
            )
        operation_result = apply_command(game)
        candidate = self._build_candidate(
            identity=identity,
            game=game,
            game_id=stored.game_id,
            version=stored.version + 1,
            scenario_id=stored.scenario_id,
            scenario_version=stored.scenario_version,
            operation_result=operation_result,
            serialize_response=serialize_response,
        )
        receipt = self._committer.execute(
            candidate, identity, game_id, expected
        )
        return self._reconciler.authoritative_response(receipt, identity)

    @staticmethod
    def _validate_expiries(game_expiry_seconds, receipt_expiry_seconds):
        if not positive_integer(game_expiry_seconds):
            raise ValueError("game_expiry_seconds must be a positive integer")
        if not positive_integer(receipt_expiry_seconds):
            raise ValueError(
                "receipt_expiry_seconds must be a positive integer"
            )

    def _identity(self, request, creation):
        if not isinstance(request, CommandRequest):
            raise CommandErrorTranslator.error(400, "invalidIdempotencyKey")
        expected = request.expected_game_version
        if creation:
            if expected is not None:
                raise CommandErrorTranslator.error(
                    400, "invalidExpectedGameVersion"
                )
        elif expected is None:
            raise CommandErrorTranslator.error(
                428, "expectedGameVersionRequired"
            )
        elif not positive_integer(expected):
            raise CommandErrorTranslator.error(
                400, "invalidExpectedGameVersion"
            )
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
            raise CommandErrorTranslator.error(400, code) from None

    def _load_game(self, game_id):
        try:
            return self._repository.load_game(game_id)
        except Exception as error:
            raise CommandErrorTranslator.translate_read(
                error, game_id=game_id
            ) from None

    def _decode_game(self, stored, game_id):
        try:
            return self._codec.decode(stored)
        except SavedGameIncompatibleError as error:
            raise CommandErrorTranslator.translate(
                error, game_id=game_id
            ) from None

    def _build_candidate(self, **kwargs):
        try:
            return self._candidate_builder.build(**kwargs)
        except SavedGameIncompatibleError as error:
            raise CommandErrorTranslator.translate(
                error, game_id=kwargs["game_id"]
            ) from None

    @staticmethod
    def _created_game(value):
        if isinstance(value, CreatedGame):
            created = value
        elif isinstance(value, tuple) and len(value) == 3:
            created = CreatedGame(*value)
        elif isinstance(value, tuple) and len(value) == 2:
            game, scenario_version = value
            created = CreatedGame(
                game, getattr(game, "scenario_id", None), scenario_version
            )
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
