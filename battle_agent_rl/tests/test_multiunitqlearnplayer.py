import unittest
import uuid

from battle_agent_rl.multiunitqlearn import MulitUnitQLearnPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestMultiUnitQLearnPlayer(unittest.TestCase):
    def setUp(self) -> None:
        self.board = Board(3, 3)
        self.friendly_faction = Faction(
            id=uuid.uuid4(), name="Friendly", color="red"
        )
        self.enemy_faction = Faction(
            id=uuid.uuid4(), name="Enemy", color="blue"
        )
        self.player = MulitUnitQLearnPlayer(
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
        self.friend1 = Unit(
            uuid.uuid4(),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            3,
        )
        self.friend2 = Unit(
            uuid.uuid4(),
            "F2",
            self.friendly_faction,
            self.player,
            "Inf",
            2,
            2,
            1,
        )
        self.enemy = Unit(
            uuid.uuid4(),
            "E1",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            4,
            4,
            3,
        )
        self.board.add_unit(self.friend1, 1, 1)
        self.board.add_unit(self.friend2, 0, 0)
        self.board.add_unit(self.enemy, 2, 2)

    def test_movement_returns_starting_hex_plans(self):
        plans = self.player.movement()
        self.assertEqual(len(plans), 2)
        plan_map = {p.unit: p.path for p in plans}
        self.assertEqual(
            plan_map[self.friend1][0], self.board.get_hex(1, 1)
        )
        self.assertEqual(
            plan_map[self.friend2][0], self.board.get_hex(0, 0)
        )

    def test_encode_unit_state_values(self):
        state = self.player.encode_unit_state(self.friend1)
        expected = (
            self.friend1.get_strength(),
            self.enemy.get_strength(),
            0,  # eta to enemy (distance 1, move 3)
            self.friend2.get_strength(),
            2,  # eta from friend to enemy (distance 3, move 1)
            1,
        )
        self.assertEqual(state, expected)

    def test_encode_unit_state_no_enemy(self):
        self.board.remove_units(self.enemy)
        state = self.player.encode_unit_state(self.friend1)
        expected = (
            self.friend1.get_strength(),
            0,
            0,
            self.friend2.get_strength(),
            0,  # eta from friend to enemy (no enemy)
            1,
        )
        self.assertEqual(state, expected)

    def test_encode_unit_state_no_friend(self):
        self.board.remove_units(self.friend2)
        state = self.player.encode_unit_state(self.friend1)
        expected = (
            self.friend1.get_strength(),
            self.enemy.get_strength(),
            0,  # eta to enemy remains 0 (distance 1)
            0,
            0,
            0,
        )
        self.assertEqual(state, expected)

    def test_encode_unit_state_unit_removed(self):
        self.board.remove_units(self.friend1)
        state = self.player.encode_unit_state(self.friend1)
        expected = (
            self.friend1.get_strength(),
            0,
            0,
            0,
            0,
            0,
        )
        self.assertEqual(state, expected)

    def test_distance_to_eta_bin(self):
        move = 4
        self.assertEqual(self.player._distance_to_eta_bin(3, move), 0)
        self.assertEqual(self.player._distance_to_eta_bin(4, move), 0)
        self.assertEqual(self.player._distance_to_eta_bin(5, move), 1)
        self.assertEqual(self.player._distance_to_eta_bin(8, move), 1)
        self.assertEqual(self.player._distance_to_eta_bin(9, move), 2)
        self.assertEqual(self.player._distance_to_eta_bin(20, move), 3)


if __name__ == "__main__":
    unittest.main()
