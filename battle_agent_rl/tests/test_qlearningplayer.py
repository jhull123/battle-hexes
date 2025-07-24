import unittest
import uuid

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestQLearningPlayerCalculateReward(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)
        self.friendly_faction = Faction(
            id=uuid.uuid4(), name="Friendly", color="red"
        )
        self.enemy_faction = Faction(
            id=uuid.uuid4(), name="Enemy", color="blue"
        )
        self.player = QLearningPlayer(
            name="AI",
            type=PlayerType.CPU,
            factions=[self.friendly_faction],
            board=self.board,
        )
        self.enemy_player = Player(
            name="Opponent",
            type=PlayerType.CPU,
            factions=[self.enemy_faction],
        )

    def test_single_pair_reward(self):
        friend = Unit(
            uuid.uuid4(),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            3,
        )
        enemy = Unit(
            uuid.uuid4(),
            "E1",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            2,
            2,
            3,
        )
        self.board.add_unit(friend, 0, 0)
        self.board.add_unit(enemy, 1, 0)

        reward = self.player.calculate_reward()
        self.assertEqual(reward, 2)

    def test_multiple_units_reward(self):
        f1 = Unit(
            uuid.uuid4(),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            4,
            2,
            3,
        )
        f2 = Unit(
            uuid.uuid4(),
            "F2",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            2,
            3,
        )
        e1 = Unit(
            uuid.uuid4(),
            "E1",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            1,
            2,
            3,
        )
        e2 = Unit(
            uuid.uuid4(),
            "E2",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            4,
            4,
            3,
        )

        self.board.add_unit(f1, 0, 0)
        self.board.add_unit(f2, 2, 1)
        self.board.add_unit(e1, 1, 0)
        self.board.add_unit(e2, 4, 3)

        reward = self.player.calculate_reward()
        self.assertAlmostEqual(reward, 2.6666666666666665)


if __name__ == "__main__":
    unittest.main()
