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
            3,
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
        friend1_hex = self.board.get_hex(1, 1)
        enemy_hex = self.board.get_hex(2, 2)
        friend2_hex = self.board.get_hex(0, 0)
        expected = (
            self.friend1.get_strength(),
            self.enemy.get_strength(),
            Board.hex_distance(friend1_hex, enemy_hex),
            self.friend2.get_strength(),
            Board.hex_distance(friend1_hex, friend2_hex),
            1,
        )
        self.assertEqual(state, expected)

    def test_encode_unit_state_no_enemy(self):
        self.board.remove_units(self.enemy)
        state = self.player.encode_unit_state(self.friend1)
        friend1_hex = self.board.get_hex(1, 1)
        friend2_hex = self.board.get_hex(0, 0)
        expected = (
            self.friend1.get_strength(),
            0,
            0,
            self.friend2.get_strength(),
            Board.hex_distance(friend1_hex, friend2_hex),
            1,
        )
        self.assertEqual(state, expected)

    def test_encode_unit_state_no_friend(self):
        self.board.remove_units(self.friend2)
        state = self.player.encode_unit_state(self.friend1)
        friend1_hex = self.board.get_hex(1, 1)
        enemy_hex = self.board.get_hex(2, 2)
        expected = (
            self.friend1.get_strength(),
            self.enemy.get_strength(),
            Board.hex_distance(friend1_hex, enemy_hex),
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


if __name__ == "__main__":
    unittest.main()
