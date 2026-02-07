import unittest

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.scoretracker import ScoreTracker
from battle_hexes_core.game.objective import Objective
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestScoreTracker(unittest.TestCase):
    def test_add_points_accumulates(self):
        player = Player(
            name="Alice",
            type=PlayerType.HUMAN,
            factions=[Faction(id="f1", name="F1", color="#fff")],
        )
        tracker = ScoreTracker([player])

        tracker.add_points(player, 3)
        tracker.add_points(player, 2)

        self.assertEqual(tracker.get_score(player), 5)


class TestObjectiveScorer(unittest.TestCase):
    def setUp(self):
        self.board = Board(4, 4)
        self.objective = Objective(coords=(1, 1), points=2, type="hold")
        self.board.get_hex(1, 1).objectives.append(self.objective)

        self.faction_one = Faction(id="f1", name="Alpha", color="#aaa")
        self.faction_two = Faction(id="f2", name="Beta", color="#bbb")
        self.player_one = Player(
            name="Alice", type=PlayerType.HUMAN, factions=[self.faction_one]
        )
        self.player_two = Player(
            name="Bob", type=PlayerType.CPU, factions=[self.faction_two]
        )

    def test_awards_points_for_held_objective(self):
        unit = Unit(
            id="u1",
            name="Unit",
            faction=self.faction_one,
            player=self.player_one,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        self.board.add_unit(unit, 1, 1)
        game = Game([self.player_one, self.player_two], self.board)

        scorer = ObjectiveScorer()
        points = scorer.award_hold_objectives(game)

        self.assertEqual(points, 2)
        self.assertEqual(
            game.get_score_tracker().get_score(self.player_one), 2
        )

    def test_awards_once_per_objective(self):
        unit_one = Unit(
            id="u1",
            name="Unit One",
            faction=self.faction_one,
            player=self.player_one,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        unit_two = Unit(
            id="u2",
            name="Unit Two",
            faction=self.faction_one,
            player=self.player_one,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        self.board.add_unit(unit_one, 1, 1)
        self.board.add_unit(unit_two, 1, 1)
        game = Game([self.player_one, self.player_two], self.board)

        scorer = ObjectiveScorer()
        points = scorer.award_hold_objectives(game)

        self.assertEqual(points, 2)
        self.assertEqual(
            game.get_score_tracker().get_score(self.player_one), 2
        )

    def test_skips_objective_when_unit_in_combat(self):
        unit = Unit(
            id="u1",
            name="Unit",
            faction=self.faction_one,
            player=self.player_one,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        enemy = Unit(
            id="u2",
            name="Enemy",
            faction=self.faction_two,
            player=self.player_two,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        self.board.add_unit(unit, 1, 1)
        self.board.add_unit(enemy, 2, 1)
        game = Game([self.player_one, self.player_two], self.board)

        scorer = ObjectiveScorer()
        points = scorer.award_hold_objectives(game)

        self.assertEqual(points, 0)
        self.assertEqual(
            game.get_score_tracker().get_score(self.player_one), 0
        )
