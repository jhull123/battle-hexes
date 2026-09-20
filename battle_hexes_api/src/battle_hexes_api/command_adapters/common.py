"""Shared command-adapter behavior."""


class GameAlreadyCompletedError(RuntimeError):
    """Raised when a command targets a game that has already completed."""


def reject_completed_game(game) -> None:
    """Reject a terminal game before a command can mutate it."""

    if getattr(game.get_game_status(), "state", None) == "completed":
        raise GameAlreadyCompletedError("Game is already completed")


def notify_game_completion(game) -> None:
    """Run state-affecting completion callbacks inside the command boundary."""

    if game.is_game_over():
        for player in game.get_players():
            player.end_game_cb()
