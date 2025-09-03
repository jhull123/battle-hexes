from __future__ import annotations
from enum import Enum
import logging

from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.gameplayer import GamePlayer
from typing import Tuple


logger = logging.getLogger(__name__)


class AgentTrainer:
    def __init__(
        self,
        gamefactory: GameFactory,
        episodes: int = 100,
        max_turns: int | None = None,
    ):
        self.gamefactory = gamefactory
        self.episodes = episodes
        self.max_turns = max_turns

    def train(self) -> GameResults:
        # TODO turn counting not supported
        results = GameResults()
        for episode in range(self.episodes):
            game = self.gamefactory.create_game()
            logger.info("")
            logger.info("Starting game %d/%d", episode + 1, self.episodes)
            GamePlayer(game).play(max_turns=self.max_turns)
            results.add_result(GameResult(self.evaluate_game(game), 1))
        return results
            
    def evaluate_game(self, game) -> GameOutcome:
        if not game.is_game_over():
            return GameOutcome.DRAW
        
        # Gather active units on the board
        units = [u for u in game.get_board().get_units() if u.get_coords() is not None]

        players = game.get_players()
        player1, player2 = players[0], players[1]

        # p1_count = sum(1 for u in units if u.player == player1)
        p2_count = sum(1 for u in units if u.player == player2)
        
        # Game is over: decide outcome from player2's perspective
        # TODO hard-coded unit counts
        if p2_count == 2:
            outcome = GameOutcome.WIN
        elif p2_count == 0:
            outcome = GameOutcome.LOSS
        else:
            outcome = GameOutcome.EXCHANGE
        
        return outcome


class GameOutcome(Enum):
    WIN = "WIN"
    EXCHANGE = "EXCHANGE"
    LOSS = "LOSS"
    DRAW = "DRAW"


class GameResult:
    def __init__(self, outcome: GameOutcome, turns: int):
        self.outcome = outcome
        self.turns = turns


class GameResults:
    def __init__(self):
        self.results = []

    def add_result(self, result: GameResult):
        self.results.append(result)

    def get_results(self):
        return self.results

    def count_wins(self):
        return len([r for r in self.results if r.outcome == GameOutcome.WIN])

    def count_losses(self):
        return len([r for r in self.results if r.outcome == GameOutcome.LOSS])

    def count_draws(self):
        return len([r for r in self.results if r.outcome == GameOutcome.DRAW])

    def count_exchanges(self):
        return len([r for r in self.results if r.outcome == GameOutcome.EXCHANGE])

    def get_avg_turns(self):
        if not self.results:
            return 0
        total_turns = sum(r.turns for r in self.results)
        return total_turns / len(self.results)
