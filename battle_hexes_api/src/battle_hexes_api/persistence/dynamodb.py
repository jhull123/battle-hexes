"""Atomic DynamoDB implementation of the game repository contract."""

from botocore.exceptions import BotoCoreError, ClientError

from .contracts import CommandIdentity
from .dynamodb_codec import (
    decode_game,
    decode_receipt,
    encode_game,
    encode_receipt,
    game_key,
    receipt_key,
)
from .dynamodb_requests import (
    commit_transaction,
    create_transaction,
)
from .errors import (
    GameAlreadyExistsError,
    GameNotFoundError,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceUnavailableError,
)


class GameRepositoryDynamoDB:
    """Persist snapshots and receipts in conditional DynamoDB transactions."""

    def __init__(self, table_name, client, clock, item_sizer, item_budget):
        if not isinstance(table_name, str) or not table_name:
            raise ValueError("table_name must be a non-empty string")
        self._table_name = table_name
        self._client = client
        self._clock = clock
        self._item_sizer = item_sizer
        self._item_budget = item_budget

    def load_game(self, game_id):
        if not isinstance(game_id, str) or not game_id:
            raise ValueError("game_id must be a non-empty string")
        game = self._read_game(game_id)
        if game is None or game.expires_at <= self._now():
            raise GameNotFoundError(game_id)
        return game

    def find_receipt(self, key_digest):
        self._validate_digest(key_digest)
        receipt = self._read_receipt(key_digest)
        if receipt is None or receipt.expires_at <= self._now():
            return None
        return receipt

    def create_game(self, game, receipt):
        if game.version != 1:
            raise ValueError("a newly created game must have version 1")
        self._validate_pair(game, receipt)
        now = self._now()
        replay = self._reconcile_receipt(receipt, now)
        if replay is not None:
            return replay
        game_item, receipt_item = self._prepare_items(game, receipt)
        request = create_transaction(
            self._table_name, game_item, receipt_item, now
        )
        try:
            self._client.transact_write_items(**request)
        except (BotoCoreError, ClientError) as error:
            return self._reconcile_create(error, game, receipt, now)
        return decode_receipt(receipt_item, receipt.identity.key_digest)

    def commit_command(self, expected_version, game, receipt):
        self._validate_expected_version(expected_version, game.version)
        self._validate_pair(game, receipt)
        now = self._now()
        replay = self._reconcile_receipt(receipt, now)
        if replay is not None:
            return replay
        game_item, receipt_item = self._prepare_items(game, receipt)
        request = commit_transaction(
            self._table_name,
            game_key(game.game_id),
            game_item,
            receipt_item,
            expected_version,
            now,
        )
        try:
            self._client.transact_write_items(**request)
        except (BotoCoreError, ClientError):
            return self._reconcile_commit(
                expected_version, game, receipt, now
            )
        return decode_receipt(receipt_item, receipt.identity.key_digest)

    def _prepare_items(self, game, receipt):
        game_item = encode_game(game)
        receipt_item = encode_receipt(receipt)
        game_size = self._item_sizer.size_bytes(game_item)
        self._item_budget.require_fits("game", game_size)
        receipt_size = self._item_sizer.size_bytes(receipt_item)
        self._item_budget.require_fits("receipt", receipt_size)
        return game_item, receipt_item

    def _reconcile_create(self, error, game, receipt, now):
        replay = self._reconcile_receipt(receipt, now)
        if replay is not None:
            return replay
        if self._is_known_create_game_race(error):
            current = self._read_game(game.game_id)
            if current is not None and current.expires_at > now:
                raise GameAlreadyExistsError(game.game_id)
        raise PersistenceUnavailableError()

    def _reconcile_commit(self, expected_version, game, receipt, now):
        replay = self._reconcile_receipt(receipt, now)
        if replay is not None:
            return replay
        current = self._read_game(game.game_id)
        if current is None or current.expires_at <= now:
            raise GameNotFoundError(game.game_id)
        if current.version != expected_version:
            raise GameVersionConflictError(
                expected_version, current.version
            )
        raise PersistenceUnavailableError()

    def _reconcile_receipt(self, candidate, now):
        existing = self._read_receipt(candidate.identity.key_digest)
        if existing is None or existing.expires_at <= now:
            return None
        if (existing.identity.request_fingerprint !=
                candidate.identity.request_fingerprint):
            raise IdempotencyConflictError(candidate.identity.key_digest)
        return existing

    def _read_game(self, game_id):
        item = self._get_item(game_key(game_id))
        return None if item is None else decode_game(item, game_id)

    def _read_receipt(self, key_digest):
        item = self._get_item(receipt_key(key_digest))
        return None if item is None else decode_receipt(item, key_digest)

    def _get_item(self, key):
        try:
            response = self._client.get_item(
                TableName=self._table_name,
                Key=key,
                ConsistentRead=True,
            )
            if not isinstance(response, dict):
                raise TypeError
            return response.get("Item")
        except (BotoCoreError, ClientError, KeyError, TypeError, ValueError):
            raise PersistenceUnavailableError() from None

    @staticmethod
    def _is_known_create_game_race(error):
        if not isinstance(error, ClientError):
            return False
        response = error.response
        if response.get("Error", {}).get("Code") != \
                "TransactionCanceledException":
            return False
        reasons = response.get("CancellationReasons")
        if not isinstance(reasons, list) or len(reasons) != 2:
            return False
        codes = [reason.get("Code") for reason in reasons
                 if isinstance(reason, dict)]
        return (len(codes) == 2 and codes[0] == "ConditionalCheckFailed"
                and codes[1] in ("None", None))

    def _now(self):
        now = self._clock.now()
        if isinstance(now, bool) or not isinstance(now, int) or now < 0:
            raise ValueError("clock must return a non-negative integer epoch")
        return now

    @staticmethod
    def _validate_pair(game, receipt):
        if receipt.game_id != game.game_id:
            raise ValueError("receipt and candidate game IDs must match")
        if receipt.game_version != game.version:
            raise ValueError("receipt and candidate game versions must match")

    @staticmethod
    def _validate_expected_version(expected_version, candidate_version):
        if (isinstance(expected_version, bool)
                or not isinstance(expected_version, int)
                or expected_version < 1):
            raise ValueError("expected_version must be a positive integer")
        if candidate_version != expected_version + 1:
            raise ValueError(
                "candidate game version must follow expected_version"
            )

    @staticmethod
    def _validate_digest(key_digest):
        CommandIdentity(key_digest, "0" * 64)
