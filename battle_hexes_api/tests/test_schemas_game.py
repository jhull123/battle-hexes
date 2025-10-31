import unittest

from battle_hexes_api.schemas.game import GameModel
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType


class TestGameModel(unittest.TestCase):
    def test_from_game_matches_game_state(self):
        board = Board(3, 4)
        player = Player(name="Test", type=PlayerType.HUMAN, factions=[])
        game = Game([player], board)

        model = GameModel.from_game(game)

        self.assertEqual(model.id, game.get_id())
        self.assertEqual(model.players, game.get_players())
        self.assertEqual(model.board, board.to_board_model())
