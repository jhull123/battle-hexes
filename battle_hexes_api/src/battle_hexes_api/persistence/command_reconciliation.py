"""Receipt-first replay and bounded reconciliation for command commits."""

from .command_errors import CommandErrorTranslator
from .command_response import CommandResponseFinalizer
from .contracts import CommandReceipt
from .errors import GameNotFoundError


class CommandReconciler:
    """Resolve receipt lookup and ambiguous commits from durable records."""

    def __init__(self, repository):
        self._repository = repository

    def find_initial_receipt(self, identity):
        """Load a replay before any command behavior is invoked."""
        try:
            receipt = self._repository.find_receipt(identity.key_digest)
        except Exception as error:
            raise CommandErrorTranslator.translate_read(error) from None
        return self._matching_receipt_or_none(receipt, identity)

    def reconcile_creation(self, identity):
        receipt = self._reconciliation_receipt(identity)
        if receipt is None:
            raise CommandErrorTranslator.unavailable()
        return receipt

    def reconcile_execution(self, identity, game_id, expected):
        receipt = self._reconciliation_receipt(identity)
        if receipt is not None:
            return receipt
        try:
            stored = self._repository.load_game(game_id)
        except GameNotFoundError:
            raise CommandErrorTranslator.error(
                404, "gameNotFound", game_id=game_id
            ) from None
        except Exception:
            raise CommandErrorTranslator.unavailable() from None
        if stored.version != expected:
            raise CommandErrorTranslator.version_conflict(
                game_id, expected, stored.version
            )
        raise CommandErrorTranslator.unavailable()

    def authoritative_response(self, receipt, identity):
        """Validate a returned receipt before replaying its exact response."""
        if not isinstance(receipt, CommandReceipt):
            raise CommandErrorTranslator.unavailable()
        self._require_matching_receipt(receipt, identity)
        return CommandResponseFinalizer.from_receipt(receipt)

    def _reconciliation_receipt(self, identity):
        try:
            receipt = self._repository.find_receipt(identity.key_digest)
        except Exception:
            raise CommandErrorTranslator.unavailable() from None
        return self._matching_receipt_or_none(receipt, identity)

    def _matching_receipt_or_none(self, receipt, identity):
        if receipt is None:
            return None
        if not isinstance(receipt, CommandReceipt):
            raise CommandErrorTranslator.unavailable()
        self._require_matching_receipt(receipt, identity)
        return receipt

    @staticmethod
    def _require_matching_receipt(receipt, identity):
        if receipt.identity.key_digest != identity.key_digest:
            raise CommandErrorTranslator.unavailable()
        fingerprints_match = (
            receipt.identity.request_fingerprint
            == identity.request_fingerprint
        )
        if not fingerprints_match:
            raise CommandErrorTranslator.error(
                409, "idempotencyKeyReused"
            )
