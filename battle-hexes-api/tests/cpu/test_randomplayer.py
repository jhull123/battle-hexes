import unittest
import uuid
from src.cpu.randomplayer import RandomPlayer
from src.game.board import Board
from src.game.game import Game
from src.game.player import Player, PlayerType
from src.unit.faction import Faction
from src.unit.unit import Unit
import random


class TestRandomPlayer(unittest.TestCase):
    def setUp(self):
        self._random_state = random.getstate()
        random.seed(44)

        self.board = Board(10, 10)
        self.blue_faction = Faction(id=uuid.uuid4(), name='Blue', color='blue')
        self.blue_player = Player(
            name='Blue Player',
            type=PlayerType.CPU,
            factions=[self.blue_faction],
        )
        self.blue_player_rando = RandomPlayer(
            player=self.blue_player,
            board=self.board
        )
        self.game = Game(players=[self.blue_player], board=self.board)
        self.blue1 = Unit(
            uuid.uuid4(),
            'Blue Unit 1',
            self.blue_faction,
            self.blue_player,
            'Infantry',
            2, 1, 3
        )
        self.board.add_unit(self.blue1, 5, 5)

    def tearDown(self):
        # Restore the original random state
        random.setstate(self._random_state)

    def test_empty_test(self):
        moves = self.blue_player_rando.movement()
        print("Moves:", moves)
        # TODO more test logic here !

    # def test_no_moves_for_empty_board(self):
    #     moves = self.blue_player.movement(self.game)
    #     self.assertEqual(moves, [], "Expected no moves for an empty board")

    # def test_move_one_unit(self):
    #     self.board.add_unit(self.blue1, 5, 5)
    #     moves = self.blue_player.movement(self.game)
    #     self.assertGreater(
    # len(moves), 0, "Expected at least one move for the unit")
