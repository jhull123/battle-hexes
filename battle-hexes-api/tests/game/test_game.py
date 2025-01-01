import unittest
from game.game import Game

class TestGame(unittest.TestCase):
    def test_game_id_is_unique(self):
        game1 = Game()
        game2 = Game()
        self.assertNotEqual(game1.get_id(), game2.get_id(), "Game IDs should be unique")

if __name__ == '__main__':
    unittest.main()
