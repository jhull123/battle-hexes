import unittest
import uuid
import os

from battle_agent_rl.qlearningplayer import (
    QLearningPlayer,
    ActionIntent,
    ActionMagnitude,
)
from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.combat.combatresults import CombatResults
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


class TestQLearningPlayerQUpdates(unittest.TestCase):
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
            alpha=0.5,
            gamma=0.0,
            epsilon=0.0,
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
        self.board.add_unit(self.friend, 0, 0)
        self.board.add_unit(self.enemy, 1, 0)

    def test_q_table_update_after_movement(self):
        self.player.movement()
        _, state, action = self.player._last_actions[self.friend.get_id()]
        self.player.movement_cb()
        expected_q = 0.5 * 2  # alpha * reward
        self.assertAlmostEqual(
            self.player._q_table[(state, action)], expected_q
        )

    def test_combat_results_updates_q_table(self):
        state = self.player.encode_unit_state(self.friend)
        action = (ActionIntent.HOLD, ActionMagnitude.NONE)
        self.player._last_actions = {
            self.friend.get_id(): (self.friend, state, action)
        }

        results = CombatResults()
        results.add_battle(
            CombatResultData((1, 1), 1, CombatResult.DEFENDER_ELIMINATED)
        )
        self.board.remove_units(self.enemy)

        self.player.combat_results(results)

        # With a combat bonus of 100 and alpha=0.5 the expected Q-value
        # update is 500.0 when a single unit is eliminated.
        self.assertEqual(self.player._q_table[(state, action)], 500.0)


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


class TestQLearningPlayerSaveLoad(unittest.TestCase):
    def setUp(self):
        self.board = Board(1, 1)
        self.faction = Faction(id=uuid.uuid4(), name="F", color="red")
        self.file_path = "qtable_test.pkl"

    def tearDown(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def build_player(self) -> QLearningPlayer:
        return QLearningPlayer(
            name="AI",
            type=PlayerType.CPU,
            factions=[self.faction],
            board=self.board,
            turn_penalty=0,
        )

    def test_save_and_load(self):
        player = self.build_player()
        state = (1, 2, 3)
        action = (ActionIntent.HOLD, ActionMagnitude.NONE)
        player._q_table[(state, action)] = 4.2
        player.save_q_table(self.file_path)

        new_player = self.build_player()
        new_player.load_q_table(self.file_path)
        self.assertEqual(new_player._q_table, player._q_table)


class TestQLearningPlayerTurnPenalty(unittest.TestCase):
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
            alpha=1.0,
            gamma=0.0,
            epsilon=0.0,
            turn_penalty=1.0,
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
            0,
        )
        self.enemy = Unit(
            uuid.uuid4(),
            "E1",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            2,
            2,
            0,
        )
        self.board.add_unit(self.friend, 0, 0)
        self.board.add_unit(self.enemy, 1, 0)

    def test_reward_decreases_each_turn(self):
        for expected in [1.0, 0.0]:
            self.player.movement()
            _, state, action = self.player._last_actions[self.friend.get_id()]
            self.player.movement_cb()
            q_val = self.player._q_table[(state, action)]
            self.assertAlmostEqual(q_val, expected)


if __name__ == "__main__":
    unittest.main()
