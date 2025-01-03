import unittest
from game.board import Board
from game.game import Game

class TestGame(unittest.TestCase):
    def test_game_id_is_unique(self):
        game1 = Game(Board(5, 5))
        game2 = Game(Board(5, 5))
        self.assertNotEqual(game1.get_id(), game2.get_id(), "Game IDs should be unique")

    def test_game_board_is_initialized(self):
        board = Board(5, 5)
        game = Game(board)
        self.assertIs(game.get_board(), board, "Game board should be initialized")

if __name__ == '__main__':
    unittest.main()
