from src.game.board import Board
from src.unit.unit import Unit
import uuid


class Game:
    def __init__(self, board):
        self.id = str(uuid.uuid4())
        self.board = board

    def get_id(self):
        return self.id

    def get_board(self):
        return self.board

    @staticmethod
    def create_sample_game():
        game = Game(Board(10, 10))
        game.board.add_unit(Unit(), 6, 4)
        game.board.add_unit(Unit(), 3, 5)
        return game
