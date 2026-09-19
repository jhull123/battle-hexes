"""Thread-safe, provider-independent in-memory game persistence."""

from threading import Lock

from .contracts import CommandIdentity, CommandReceipt, StoredGame
from .errors import (
    GameAlreadyExistsError,
    GameNotFoundError,
    GameVersionConflictError,
    IdempotencyConflictError,
)


def _copy_bytes(value):
    return memoryview(value).tobytes()


def _copy_game(game):
    return StoredGame(
        game_id=game.game_id,
        version=game.version,
        state_schema_version=game.state_schema_version,
        scenario_id=game.scenario_id,
        scenario_version=game.scenario_version,
        state=_copy_bytes(game.state),
        updated_at=game.updated_at,
        expires_at=game.expires_at,
    )


def _copy_receipt(receipt):
    identity = CommandIdentity(
        key_digest=receipt.identity.key_digest,
        request_fingerprint=receipt.identity.request_fingerprint,
    )
    return CommandReceipt(
        identity=identity,
        game_id=receipt.game_id,
        game_version=receipt.game_version,
        status_code=receipt.status_code,
        content_type=receipt.content_type,
        response_body=_copy_bytes(receipt.response_body),
        response_headers=dict(receipt.response_headers),
        created_at=receipt.created_at,
        expires_at=receipt.expires_at,
    )


def _game_item(game):
    return {
        "pk": f"GAME#{game.game_id}",
        "sk": "SNAPSHOT",
        "item_type": "game",
        "game_id": game.game_id,
        "version": game.version,
        "state_schema_version": game.state_schema_version,
        "scenario_id": game.scenario_id,
        "scenario_version": game.scenario_version,
        "state": _copy_bytes(game.state),
        "updated_at": game.updated_at,
        "ttl": game.expires_at,
    }


def _receipt_item(receipt):
    return {
        "pk": f"IDEMPOTENCY#{receipt.identity.key_digest}",
        "sk": "RECEIPT",
        "item_type": "command_receipt",
        "request_hash": receipt.identity.request_fingerprint,
        "game_id": receipt.game_id,
        "game_version": receipt.game_version,
        "status_code": receipt.status_code,
        "content_type": receipt.content_type,
        "response_body": _copy_bytes(receipt.response_body),
        "response_headers": dict(receipt.response_headers),
        "created_at": receipt.created_at,
        "ttl": receipt.expires_at,
    }


class GameRepositoryInMemory:
    """Store detached persistence values with atomic game/receipt commits."""

    def __init__(self, clock, item_sizer, item_budget):
        self._clock = clock
        self._item_sizer = item_sizer
        self._item_budget = item_budget
        self._lock = Lock()
        self._state = ({}, {})

    def load_game(self, game_id):
        with self._lock:
            now = self._clock.now()
            games, _ = self._state
            game = games.get(game_id)
            if game is None or game.expires_at <= now:
                raise GameNotFoundError(game_id)
            return _copy_game(game)

    def find_receipt(self, key_digest):
        with self._lock:
            now = self._clock.now()
            _, receipts = self._state
            receipt = receipts.get(key_digest)
            if receipt is None or receipt.expires_at <= now:
                return None
            return _copy_receipt(receipt)

    def create_game(self, game, receipt):
        if game.version != 1:
            raise ValueError("a newly created game must have version 1")
        self._validate_pair(game, receipt)
        candidate_game = _copy_game(game)
        candidate_receipt = _copy_receipt(receipt)

        with self._lock:
            now = self._clock.now()
            replay = self._find_replay(candidate_receipt, now)
            if replay is not None:
                return replay
            self._require_capacity(candidate_game, candidate_receipt)
            games, receipts = self._state
            current = games.get(candidate_game.game_id)
            if current is not None and current.expires_at > now:
                raise GameAlreadyExistsError(candidate_game.game_id)
            result = _copy_receipt(candidate_receipt)
            self._publish(candidate_game, candidate_receipt)
            return result

    def commit_command(self, expected_version, game, receipt):
        if (
            isinstance(expected_version, bool)
            or not isinstance(expected_version, int)
            or expected_version < 1
        ):
            raise ValueError("expected_version must be a positive integer")
        if game.version != expected_version + 1:
            raise ValueError(
                "candidate game version must follow expected_version"
            )
        self._validate_pair(game, receipt)
        candidate_game = _copy_game(game)
        candidate_receipt = _copy_receipt(receipt)

        with self._lock:
            now = self._clock.now()
            replay = self._find_replay(candidate_receipt, now)
            if replay is not None:
                return replay
            self._require_capacity(candidate_game, candidate_receipt)
            games, _ = self._state
            current = games.get(candidate_game.game_id)
            if current is None or current.expires_at <= now:
                raise GameNotFoundError(candidate_game.game_id)
            if current.version != expected_version:
                raise GameVersionConflictError(
                    expected_version, current.version
                )
            result = _copy_receipt(candidate_receipt)
            self._publish(candidate_game, candidate_receipt)
            return result

    @staticmethod
    def _validate_pair(game, receipt):
        if receipt.game_id != game.game_id:
            raise ValueError("receipt and candidate game IDs must match")
        if receipt.game_version != game.version:
            raise ValueError("receipt and candidate game versions must match")

    def _find_replay(self, candidate, now):
        _, receipts = self._state
        existing = receipts.get(candidate.identity.key_digest)
        if existing is None or existing.expires_at <= now:
            return None
        if (
            existing.identity.request_fingerprint
            != candidate.identity.request_fingerprint
        ):
            raise IdempotencyConflictError(candidate.identity.key_digest)
        return _copy_receipt(existing)

    def _require_capacity(self, game, receipt):
        game_size = self._item_sizer.size_bytes(_game_item(game))
        self._item_budget.require_fits("game", game_size)
        receipt_size = self._item_sizer.size_bytes(_receipt_item(receipt))
        self._item_budget.require_fits("receipt", receipt_size)

    def _publish(self, game, receipt):
        games, receipts = self._state
        next_games = dict(games)
        next_receipts = dict(receipts)
        next_games[game.game_id] = game
        next_receipts[receipt.identity.key_digest] = receipt
        self._state = (next_games, next_receipts)
