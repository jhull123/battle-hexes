import unittest
from game.board import Board
from game.game import Game
from game.gamerepo import GameRepository


class TestGameRepos(unittest.TestCase):
    def test_update_game_creates_new_game(self):
        game_repo = GameRepository()
        game = Game([], Board(5, 5))

        game_repo.update_game(game)

        game_from_repo = game_repo.get_game(game.get_id())
        self.assertEqual(game, game_from_repo)
