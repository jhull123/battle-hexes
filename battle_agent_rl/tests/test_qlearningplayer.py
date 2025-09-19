import unittest
import uuid

from battle_agent_rl.qlearningplayer import (
    QLearningPlayer,
    ActionIntent,
    ActionMagnitude,
)
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
            turn_penalty=0,
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


class TestQLearningPlayerMovePlan(unittest.TestCase):
    def setUp(self):
        self.board = Board(3, 3)
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
            turn_penalty=0,
        )
        self.enemy_player = Player(
            name="Opponent",
            type=PlayerType.CPU,
            factions=[self.enemy_faction],
        )
        self.friend = Unit(
            uuid.uuid4(),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            3,
        )
        self.enemy = Unit(
            uuid.uuid4(),
            "E1",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            2,
            2,
            3,
        )
        self.board.add_unit(self.friend, 2, 1)
        self.board.add_unit(self.enemy, 0, 1)

    def test_advance_creates_forward_path(self):
        plan = self.player.move_plan(
            self.friend, ActionIntent.ADVANCE, ActionMagnitude.HALF
        )
        coords = [(h.row, h.column) for h in plan.path]
        self.assertEqual(coords, [(2, 1), (1, 1)])

    def test_retreat_increases_distance(self):
        enemy_hex = self.board.get_hex(0, 1)
        start_hex = self.board.get_hex(2, 1)
        start_dist = Board.hex_distance(start_hex, enemy_hex)
        plan = self.player.move_plan(
            self.friend, ActionIntent.RETREAT, ActionMagnitude.HALF
        )
        end_hex = plan.path[-1]
        end_dist = Board.hex_distance(end_hex, enemy_hex)
        self.assertGreaterEqual(end_dist, start_dist)

    def test_distance_to_eta_bin(self):
        move = 4
        self.assertEqual(self.player._distance_to_eta_bin(3, move), 0)
        self.assertEqual(self.player._distance_to_eta_bin(4, move), 0)
        self.assertEqual(self.player._distance_to_eta_bin(5, move), 1)
        self.assertEqual(self.player._distance_to_eta_bin(8, move), 1)
        self.assertEqual(self.player._distance_to_eta_bin(9, move), 2)
        self.assertEqual(self.player._distance_to_eta_bin(20, move), 3)


class TestQLearningPlayerEncodePairState(unittest.TestCase):
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
            turn_penalty=0,
        )
        self.enemy_player = Player(
            name="Opponent",
            type=PlayerType.CPU,
            factions=[self.enemy_faction],
        )

    def test_eta_and_power_bins(self):
        ui = Unit(
            uuid.uuid4(),
            "U1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            3,
        )
        uj = Unit(
            uuid.uuid4(),
            "U2",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            1,
        )
        enemy = Unit(
            uuid.uuid4(),
            "E1",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            4,
            4,
            3,
        )
        self.board.add_unit(ui, 0, 0)
        self.board.add_unit(uj, 0, 2)
        self.board.add_unit(enemy, 3, 0)
        self.assertEqual(self.player._encode_pair_state(ui, uj), (2, 1))


if __name__ == "__main__":
    unittest.main()
