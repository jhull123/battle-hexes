"""Evaluate whether a game has ended and who won."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GameStatus:
    """Machine-readable game completion status."""

    state: str
    winner_player_name: str | None = None
    winner_faction_id: str | None = None
    reason: str | None = None
    message: str | None = None


class GameStatusEvaluator:
    """Determine game completion from core game state and scenario rules."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TURN_LIMIT_REACHED = "turn_limit_reached"
    OBJECTIVE_CONTROL = "objective_control"
    UNIT_ELIMINATION = "unit_elimination"
    DRAW = "draw"

    def evaluate(self, game: Game) -> GameStatus:
        """Return the current status for ``game``."""
        elimination_winner = self._unit_elimination_winner(game)
        if elimination_winner is not None:
            return self._completed(
                game,
                elimination_winner,
                self.UNIT_ELIMINATION,
                (
                    f"{elimination_winner.name} wins by eliminating "
                    "all enemy units."
                ),
            )

        if self._turn_limit_reached(game):
            winner = self._score_winner(game)
            reason = self._turn_limit_reason(game)
            message = self._score_message(game, winner)
            return self._completed(game, winner, reason, message)

        return GameStatus(state=self.IN_PROGRESS)

    def _turn_limit_reached(self, game: Game) -> bool:
        turn_limit = getattr(game, "turn_limit", None)
        if turn_limit is None:
            turn_limit = game.get_turn_limit()
        turn_number = getattr(game, "turn_number", None)
        if turn_number is None:
            turn_number = game.get_turn_number()
        if not (
            isinstance(turn_limit, int)
            and isinstance(turn_number, int)
        ):
            return False
        return turn_number > turn_limit

    def _turn_limit_reason(self, game: Game) -> str:
        victory = getattr(game, "victory", None)
        if victory is not None and victory.method == self.OBJECTIVE_CONTROL:
            return self.OBJECTIVE_CONTROL
        return self.TURN_LIMIT_REACHED

    def _unit_elimination_winner(self, game: Game) -> Player | None:
        active_players = self._active_players(game)
        if len(active_players) == 1:
            return active_players[0]
        return None

    def _score_winner(self, game: Game) -> Player | None:
        players = game.get_players() if hasattr(game, "get_players") else []
        if not players:
            return None
        score_tracker = game.get_score_tracker()
        scores = [
            (player, score_tracker.get_score(player))
            for player in players
        ]
        high_score = max(score for _, score in scores)
        winners = [player for player, score in scores if score == high_score]
        if len(winners) == 1:
            return winners[0]
        return None

    def _score_message(self, game: Game, winner: Player | None) -> str:
        scores = game.get_score_tracker().get_scores()
        if winner is None:
            return f"Game completed in a draw. Scores: {scores}."
        return f"{winner.name} wins. Scores: {scores}."

    def _completed(
        self,
        game: Game,
        winner: Player | None,
        reason: str,
        message: str,
    ) -> GameStatus:
        status = GameStatus(
            state=self.COMPLETED,
            winner_player_name=getattr(winner, "name", None),
            winner_faction_id=self._winner_faction_id(winner),
            reason=reason if winner is not None else self.DRAW,
            message=message,
        )
        logger.info(
            "Game over detected: status=%s game_id=%s turn_number=%s "
            "turn_limit=%s scores=%s active_players=%s",
            status,
            game.get_id(),
            game.get_turn_number(),
            game.get_turn_limit(),
            game.get_score_tracker().get_scores(),
            [player.name for player in self._active_players(game)],
        )
        return status

    def _winner_faction_id(self, winner: Player | None) -> str | None:
        if winner is None or not winner.factions:
            return None
        return winner.factions[0].id

    def _active_players(self, game: Game) -> list[Player]:
        active_players = []
        players = game.get_players() if hasattr(game, "get_players") else []
        if not isinstance(players, (list, tuple)):
            return active_players
        for player in players:
            units = game.get_board().get_units_for_player(player)
            if not isinstance(units, (list, tuple)):
                continue
            if any(unit.get_coords() is not None for unit in units):
                active_players.append(player)
        return active_players
