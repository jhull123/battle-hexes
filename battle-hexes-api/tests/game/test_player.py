import unittest
from src.game.player import Player, PlayerType


class TestPlayer(unittest.TestCase):
    def test_movement_not_implemented(self):
        player = Player(name='P1', type=PlayerType.HUMAN, factions=[])
        with self.assertRaises(NotImplementedError):
            player.movement()
