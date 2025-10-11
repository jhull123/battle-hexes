import unittest
import uuid
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit
import random


class TestRandomPlayer(unittest.TestCase):
    def setUp(self):
        self._random_state = random.getstate()
        random.seed(44)

        self.board = Board(10, 10)
        self.blue_faction = Faction(
            id=str(uuid.uuid4()), name='Blue', color='blue'
        )
        blue_player = Player(
            name='Blue Player',
            type=PlayerType.CPU,
            factions=[self.blue_faction],
        )
        self.blue_player_rando = RandomPlayer(
            name='Blue Player',
            type=PlayerType.CPU,
            factions=[self.blue_faction],
            board=self.board
        )
        self.game = Game(players=[blue_player], board=self.board)
        self.blue1 = Unit(
            str(uuid.uuid4()),
            'Blue Unit 1',
            self.blue_faction,
            blue_player,
            'Infantry',
            2, 1, 3
        )

    def tearDown(self):
        # Restore the original random state
        random.setstate(self._random_state)

    def test_no_moves_for_empty_board(self):
        moves = self.blue_player_rando.movement()
        self.assertEqual(moves, [], "Expected no moves for an empty board")

    def test_random_hex_empty(self):
        self.assertIsNone(self.blue_player_rando.random_hex(set()))

    def test_random_hex_deterministic_choice(self):
        hexes = {self.board.get_hex(1, 1), self.board.get_hex(2, 2)}
        chosen_hex = self.blue_player_rando.random_hex(hexes)
        self.assertEqual((chosen_hex.row, chosen_hex.column), (2, 2))

    def test_move_one_unit(self):
        self.board.add_unit(self.blue1, 5, 5)
        moves = self.blue_player_rando.movement()
        self.assertEqual(len(moves), 1, "Expected one movement plan")

        plan = moves[0]
        path_coords = [(hex.row, hex.column) for hex in plan.path]
        self.assertEqual(
            path_coords,
            [(5, 5), (4, 5), (3, 5)],
            "Unit should move along the expected path"
        )
