import unittest
import uuid

from battle_agent_rl.rlplayer import RLPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestRLPlayer(unittest.TestCase):
    def setUp(self):
        self.board = Board(8, 8)
        self.faction = Faction(id=uuid.uuid4(), name="Red", color="red")
        player = Player(
            name="Red Player",
            type=PlayerType.CPU,
            factions=[self.faction],
        )
        self.rl_player = RLPlayer(
            name="RL Player",
            type=PlayerType.CPU,
            factions=[self.faction],
            board=self.board,
        )
        self.game = Game(players=[player], board=self.board)
        self.unit = Unit(
            uuid.uuid4(),
            "Red Unit",
            self.faction,
            player,
            "Infantry",
            2,
            2,
            3,
        )

    def test_no_moves_on_empty_board(self):
        self.assertEqual(self.rl_player.movement(), [])

    def test_no_moves_even_with_units(self):
        self.board.add_unit(self.unit, 4, 4)
        self.assertEqual(self.rl_player.movement(), [])
