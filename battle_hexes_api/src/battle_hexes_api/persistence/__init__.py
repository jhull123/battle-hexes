"""Public storage-neutral game-persistence contracts."""

from .clock import SystemClock, is_expired
from .contracts import (
    Clock,
    CommandIdentity,
    CommandReceipt,
    EncodedItemBudget,
    EncodedItemSizer,
    GameRepository,
    StoredGame,
)
from .errors import (
    GameAlreadyExistsError,
    GameNotFoundError,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceCapacityError,
    PersistenceError,
    PersistenceUnavailableError,
    SavedGameIncompatibleError,
)
from .identity import (
    canonical_json_bytes,
    create_command_identity,
    digest_idempotency_key,
    fingerprint_request,
    normalize_method,
    normalize_route,
)
from .game_state_codec import GameStateCodec
from .in_memory import GameRepositoryInMemory
from .command_errors import CommandServiceError
from .command_models import CommandRequest, CreatedGame, SuccessfulResponse
from .command_service import GameCommandService
from .item_sizer import InMemoryItemSizer

__all__ = [
    "Clock",
    "CommandIdentity",
    "CommandReceipt",
    "CommandRequest",
    "CommandServiceError",
    "CreatedGame",
    "EncodedItemBudget",
    "EncodedItemSizer",
    "GameAlreadyExistsError",
    "GameNotFoundError",
    "GameRepository",
    "GameRepositoryInMemory",
    "GameCommandService",
    "GameStateCodec",
    "InMemoryItemSizer",
    "GameVersionConflictError",
    "IdempotencyConflictError",
    "PersistenceCapacityError",
    "PersistenceError",
    "PersistenceUnavailableError",
    "SavedGameIncompatibleError",
    "StoredGame",
    "SuccessfulResponse",
    "SystemClock",
    "canonical_json_bytes",
    "create_command_identity",
    "digest_idempotency_key",
    "fingerprint_request",
    "is_expired",
    "normalize_method",
    "normalize_route",
]
