from src.game.board import Board
from src.game.player import Player


class RandomPlayer:
    def __init__(self,
                 player: Player,
                 board: Board):
        self.player = player
        self.board = board

    def movement(self):
        # Random movement logic can be implemented here
        print(
            "RandomPlayer movement logic not implemented yet...",
            self.board,
            self.player
        )
        pass
