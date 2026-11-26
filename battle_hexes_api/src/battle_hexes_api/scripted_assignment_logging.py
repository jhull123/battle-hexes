"""Report scripted objective assignments in the server log."""

import logging
from functools import partial
from uuid import UUID

from battle_agent_rl.scripted import ScriptedPlayer
from battle_hexes_core.game.game import Game


# Inherit the server's configured log level and handler under Uvicorn.
opening_logger = logging.getLogger("uvicorn.error.scripted_opening")
reinforcement_logger = logging.getLogger(
    "uvicorn.error.scripted_reinforcements"
)


def log_scripted_openings(game: Game, mode: str) -> None:
    for player in game.players:
        if not isinstance(player, ScriptedPlayer):
            continue
        counts = player.objective_assignment_counts()
        if counts:
            split = "/".join(map(str, counts.values()))
            opening_logger.info(
                "Scripted opening split: game=%s player=%s mode=%s "
                "split=%s assignments=%s",
                game.id, player.name, mode, split, counts,
            )


def attach_reinforcement_logging(game: Game) -> None:
    """Observe new assignments on fresh games and on hydrated commands."""
    for player in game.players:
        if isinstance(player, ScriptedPlayer):
            player.on_reinforcement_assignments = partial(
                _log_reinforcement_assignments, game.id, player.name,
            )


def _log_reinforcement_assignments(
    game_id: UUID, player_name: str, entry: tuple[int, int],
    assignments: dict[str, tuple[int, int]],
) -> None:
    reinforcement_logger.info(
        "Scripted reinforcement assignments: game=%s player=%s entry=%s "
        "assignments=%s",
        game_id, player_name, entry, assignments,
    )
