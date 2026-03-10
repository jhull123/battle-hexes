from __future__ import annotations

from collections.abc import Iterable

from battle_hexes_core.game.player import Player


class ScoreTracker:
    """Track score totals for each player in a game."""

    def __init__(self, players: Iterable[Player] | None = None) -> None:
        self._scores: dict[str, int] = {}
        if players:
            for player in players:
                self._scores[self._player_key(player)] = 0

    @staticmethod
    def _player_key(player: Player) -> str:
        name = getattr(player, "name", None)
        if isinstance(name, str) and name:
            return name
        return str(player)

    def add_points(self, player: Player, points: int) -> None:
        """Add points to a player's score."""
        if points <= 0:
            return
        key = self._player_key(player)
        self._scores[key] = self._scores.get(key, 0) + points

    def set_score(self, player: Player, points: int) -> None:
        """Replace a player's score with ``points``."""
        key = self._player_key(player)
        self._scores[key] = max(0, points)

    def set_scores(
        self,
        score_updates: Iterable[tuple[Player, int]],
    ) -> None:
        """Replace multiple player score values."""
        for player, points in score_updates:
            self.set_score(player, points)

    def get_score(self, player: Player) -> int:
        """Return the current score for the given player."""
        return self._scores.get(self._player_key(player), 0)

    def get_scores(self) -> dict[str, int]:
        """Return a copy of the score table."""
        return dict(self._scores)
