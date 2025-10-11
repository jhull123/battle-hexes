import os
import pickle
import unittest
import uuid

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
            id=str(uuid.uuid4()), name="Friendly", color="red"
        )
        self.enemy_faction = Faction(
            id=str(uuid.uuid4()), name="Enemy", color="blue"
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
            str(uuid.uuid4()),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            3,
        )
        enemy = Unit(
            str(uuid.uuid4()),
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
            str(uuid.uuid4()),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            4,
            2,
            3,
        )
        f2 = Unit(
            str(uuid.uuid4()),
            "F2",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            2,
            3,
        )
        e1 = Unit(
            str(uuid.uuid4()),
            "E1",
            self.enemy_faction,
            self.enemy_player,
            "Inf",
            1,
            2,
            3,
        )
        e2 = Unit(
            str(uuid.uuid4()),
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
            id=str(uuid.uuid4()), name="Friendly", color="red"
        )
        self.enemy_faction = Faction(
            id=str(uuid.uuid4()), name="Enemy", color="blue"
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
            str(uuid.uuid4()),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            3,
        )
        self.enemy = Unit(
            str(uuid.uuid4()),
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
        # Reward is a turn penalty of ``-0.1`` which is applied after the first
        # turn. With ``alpha=0.5`` and ``gamma=0`` the updated Q-value should
        # reflect half of this reward.
        expected_q = 0.5 * -0.1  # alpha * reward
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
            CombatResultData(
                (1, 1),
                1,
                CombatResult.DEFENDER_ELIMINATED,
                ((self.friend,), (self.enemy,)),
            )
        )
        self.board.remove_units(self.enemy)

        self.player.combat_results(results)

        self.assertEqual(self.player._q_table[(state, action)], 0.0)

    def test_combat_results_only_rewards_participants(self):
        friend2 = Unit(
            str(uuid.uuid4()),
            "F2",
            self.friendly_faction,
            self.player,
            "Inf",
            1,
            1,
            3,
        )
        self.board.add_unit(friend2, 2, 0)

        state1 = self.player.encode_unit_state(self.friend)
        state2 = self.player.encode_unit_state(friend2)
        action = (ActionIntent.HOLD, ActionMagnitude.NONE)
        self.player._last_actions = {
            self.friend.get_id(): (self.friend, state1, action),
            friend2.get_id(): (friend2, state2, action),
        }

        results = CombatResults()
        results.add_battle(
            CombatResultData(
                (2, 1),
                4,
                CombatResult.DEFENDER_ELIMINATED,
                ((self.friend,), (self.enemy,)),
            )
        )

        self.player.combat_results(results)

        updated_value = self.player._q_table[(state1, action)]
        self.assertGreater(updated_value, 0.0)
        self.assertNotIn((state2, action), self.player._q_table)


class TestQLearningPlayerMovePlan(unittest.TestCase):
    def setUp(self):
        self.board = Board(3, 3)
        self.friendly_faction = Faction(
            id=str(uuid.uuid4()), name="Friendly", color="red"
        )
        self.enemy_faction = Faction(
            id=str(uuid.uuid4()), name="Enemy", color="blue"
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
            str(uuid.uuid4()),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            3,
        )
        self.enemy = Unit(
            str(uuid.uuid4()),
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


class TestQLearningPlayerSaveLoad(unittest.TestCase):
    def setUp(self):
        self.board = Board(1, 1)
        self.faction = Faction(id=str(uuid.uuid4()), name="F", color="red")
        self.file_path = "qtable_test.pkl"

    def tearDown(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def build_player(
        self,
        *,
        alpha: float = 0.1,
        gamma: float = 0.15,
        epsilon: float = 0.1,
        turn_penalty: float = 0.0,
        combat_bonus: float = 1000.0,
        ally_combat_bonus: float = 100.0,
    ) -> QLearningPlayer:
        return QLearningPlayer(
            name="AI",
            type=PlayerType.CPU,
            factions=[self.faction],
            board=self.board,
            alpha=alpha,
            gamma=gamma,
            epsilon=epsilon,
            turn_penalty=turn_penalty,
            combat_bonus=combat_bonus,
            ally_combat_bonus=ally_combat_bonus,
        )

    def test_save_and_load(self):
        player = self.build_player(
            alpha=0.25,
            gamma=0.5,
            epsilon=0.75,
            turn_penalty=0.2,
            combat_bonus=1500.0,
            ally_combat_bonus=55.0,
        )
        state = (1, 2, 3)
        action = (ActionIntent.HOLD, ActionMagnitude.NONE)
        player._q_table[(state, action)] = 4.2
        player.save_q_table(self.file_path)

        with open(self.file_path, "rb") as saved_file:
            payload = pickle.load(saved_file)

        self.assertIn("q_table", payload)
        self.assertIn("settings", payload)
        self.assertEqual(payload["q_table"], player._q_table)
        self.assertEqual(
            payload["settings"],
            {
                "alpha": player._alpha,
                "gamma": player._gamma,
                "epsilon": player._epsilon,
                "turn_penalty": player._turn_penalty,
                "combat_bonus": player._combat_bonus,
                "ally_combat_bonus": player._ally_combat_bonus,
            },
        )

        new_player = self.build_player(
            alpha=0.9,
            gamma=0.8,
            epsilon=0.7,
            turn_penalty=0.6,
            combat_bonus=500.0,
        )
        new_player.load_q_table(self.file_path)
        self.assertEqual(new_player._q_table, player._q_table)
        self.assertEqual(new_player._alpha, player._alpha)
        self.assertEqual(new_player._gamma, player._gamma)
        self.assertEqual(new_player._epsilon, player._epsilon)
        self.assertEqual(new_player._turn_penalty, player._turn_penalty)
        self.assertEqual(new_player._combat_bonus, player._combat_bonus)
        self.assertEqual(
            new_player._half_combat_bonus,
            player._half_combat_bonus,
        )
        self.assertEqual(
            new_player._double_combat_bonus,
            player._double_combat_bonus,
        )

    def test_load_legacy_format(self):
        q_table = {((1, 2, 3), (ActionIntent.HOLD, ActionMagnitude.NONE)): 9.9}
        with open(self.file_path, "wb") as legacy_file:
            pickle.dump(q_table, legacy_file)

        player = self.build_player()
        original_settings = {
            "alpha": player._alpha,
            "gamma": player._gamma,
            "epsilon": player._epsilon,
            "turn_penalty": player._turn_penalty,
            "combat_bonus": player._combat_bonus,
            "half": player._half_combat_bonus,
            "double": player._double_combat_bonus,
        }

        player.load_q_table(self.file_path)

        self.assertEqual(player._q_table, q_table)
        self.assertEqual(player._alpha, original_settings["alpha"])
        self.assertEqual(player._gamma, original_settings["gamma"])
        self.assertEqual(player._epsilon, original_settings["epsilon"])
        self.assertEqual(
            player._turn_penalty,
            original_settings["turn_penalty"],
        )
        self.assertEqual(
            player._combat_bonus,
            original_settings["combat_bonus"],
        )
        self.assertEqual(
            player._half_combat_bonus,
            original_settings["half"],
        )
        self.assertEqual(
            player._double_combat_bonus,
            original_settings["double"],
        )


class TestQLearningPlayerTurnPenalty(unittest.TestCase):
    def setUp(self):
        self.board = Board(3, 3)
        self.friendly_faction = Faction(
            id=str(uuid.uuid4()), name="Friendly", color="red"
        )
        self.enemy_faction = Faction(
            id=str(uuid.uuid4()), name="Enemy", color="blue"
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
            str(uuid.uuid4()),
            "F1",
            self.friendly_faction,
            self.player,
            "Inf",
            3,
            3,
            0,
        )
        self.enemy = Unit(
            str(uuid.uuid4()),
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
        # Each call to ``movement_cb`` applies an additional ``-0.1`` penalty.
        # With ``alpha=1.0`` the Q-value mirrors the cumulative penalty.
        for expected in [-0.1, -0.2]:
            self.player.movement()
            _, state, action = self.player._last_actions[self.friend.get_id()]
            self.player.movement_cb()
            q_val = self.player._q_table[(state, action)]
            self.assertAlmostEqual(q_val, expected)


if __name__ == "__main__":
    unittest.main()
