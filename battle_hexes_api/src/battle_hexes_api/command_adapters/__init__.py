"""Framework-neutral game command adapters and response serializers."""

from .combat_turn import CombatAdapter, CombatCommandResult, EndTurnAdapter
from .common import GameAlreadyCompletedError
from .creation import CreateGameAdapter
from .movement import (
    EndMovementAdapter,
    HumanMoveAdapter,
    MovementAdapter,
    MovementCommandResult,
)
from .serializers import (
    CombatResponseSerializer,
    CreateGameResponseSerializer,
    EndTurnResponseSerializer,
    GameResponseSerializer,
    MovementResponseSerializer,
)

__all__ = [
    "CombatAdapter",
    "CombatCommandResult",
    "CombatResponseSerializer",
    "CreateGameAdapter",
    "CreateGameResponseSerializer",
    "EndMovementAdapter",
    "EndTurnAdapter",
    "EndTurnResponseSerializer",
    "GameAlreadyCompletedError",
    "GameResponseSerializer",
    "HumanMoveAdapter",
    "MovementAdapter",
    "MovementCommandResult",
    "MovementResponseSerializer",
]
