import unittest

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.scenario.scenario import ScenarioVictory
from battle_hexes_core.scoring.game_status_evaluator import GameStatusEvaluator
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestGameStatusEvaluator(unittest.TestCase):
    def setUp(self):
        self.board = Board(3, 3)
        self.faction_one = Faction(id="f1", name="Alpha", color="#aaa")
        self.faction_two = Faction(id="f2", name="Beta", color="#bbb")
        self.player_one = Player(
            name="Alice", type=PlayerType.HUMAN, factions=[self.faction_one]
        )
        self.player_two = Player(
            name="Bob", type=PlayerType.CPU, factions=[self.faction_two]
        )
        self.unit_one = self._unit("u1", self.faction_one, self.player_one)
        self.unit_two = self._unit("u2", self.faction_two, self.player_two)
        self.board.add_unit(self.unit_one, 0, 0)
        self.board.add_unit(self.unit_two, 2, 2)
        self.game = Game([self.player_one, self.player_two], self.board)
        self.evaluator = GameStatusEvaluator()

    def _unit(self, unit_id, faction, player):
        return Unit(
            id=unit_id,
            name=unit_id,
            faction=faction,
            player=player,
            type="Infantry",
            attack=1,
            defense=1,
            move=1,
        )

    def test_in_progress_when_no_ending_condition_is_met(self):
        status = self.evaluator.evaluate(self.game)

        self.assertEqual(status.state, "in_progress")
        self.assertIsNone(status.reason)
        self.assertIsNone(status.winner_player_name)

    def test_completed_when_unit_elimination_leaves_one_player_active(self):
        self.unit_two.set_coords(None, None)

        status = self.evaluator.evaluate(self.game)

        self.assertEqual(status.state, "completed")
        self.assertEqual(status.reason, "unit_elimination")
        self.assertEqual(status.winner_player_name, "Alice")
        self.assertEqual(status.winner_faction_id, "f1")

    def test_completed_at_turn_limit_with_score_winner(self):
        self.game.turn_limit = 1
        self.game.turn_number = 2
        self.game.get_score_tracker().set_score(self.player_one, 3)
        self.game.get_score_tracker().set_score(self.player_two, 1)

        status = self.evaluator.evaluate(self.game)

        self.assertEqual(status.state, "completed")
        self.assertEqual(status.reason, "turn_limit_reached")
        self.assertEqual(status.winner_player_name, "Alice")

    def test_completed_objective_control_at_turn_limit(self):
        self.game.turn_limit = 1
        self.game.turn_number = 2
        self.game.victory = ScenarioVictory(
            method="objective_control",
            scoring_side="Alpha",
        )
        self.game.get_score_tracker().set_score(self.player_one, 1)
        self.game.get_score_tracker().set_score(self.player_two, 0)

        status = self.evaluator.evaluate(self.game)

        self.assertEqual(status.state, "completed")
        self.assertEqual(status.reason, "objective_control")
        self.assertEqual(status.winner_player_name, "Alice")


if __name__ == "__main__":
    unittest.main()


class TestGameStatusCoreWorkflow(unittest.TestCase):
    def setUp(self):
        self.board = Board(3, 3)
        self.faction_one = Faction(id="f1", name="Alpha", color="#aaa")
        self.faction_two = Faction(id="f2", name="Beta", color="#bbb")
        self.player_one = Player(
            name="Alice", type=PlayerType.HUMAN, factions=[self.faction_one]
        )
        self.player_two = Player(
            name="Bob", type=PlayerType.CPU, factions=[self.faction_two]
        )
        self.unit_one = Unit(
            id="u1",
            name="u1",
            faction=self.faction_one,
            player=self.player_one,
            type="Infantry",
            attack=1,
            defense=1,
            move=1,
        )
        self.unit_two = Unit(
            id="u2",
            name="u2",
            faction=self.faction_two,
            player=self.player_two,
            type="Infantry",
            attack=1,
            defense=1,
            move=1,
        )
        self.board.add_unit(self.unit_one, 0, 0)
        self.board.add_unit(self.unit_two, 2, 2)
        self.game = Game([self.player_one, self.player_two], self.board)

    def test_movement_result_contains_core_computed_game_status(self):
        self.unit_two.set_coords(None, None)

        result = self.game.apply_movement_plans([])

        self.assertEqual(result.game_status.state, "completed")
        self.assertEqual(result.game_status.reason, "unit_elimination")
        self.assertEqual(result.game_status.winner_player_name, "Alice")

    def test_end_turn_result_contains_core_computed_game_status(self):
        self.game.turn_limit = 1
        self.game.turn_number = 1
        self.game.current_player = self.player_two
        self.game.get_score_tracker().set_score(self.player_one, 2)
        self.game.get_score_tracker().set_score(self.player_two, 1)

        result = self.game.end_turn()

        self.assertEqual(result.game_status.state, "completed")
        self.assertEqual(result.game_status.reason, "turn_limit_reached")
        self.assertEqual(result.game_status.winner_player_name, "Alice")
