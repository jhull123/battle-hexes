import unittest

from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.objective import Objective
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.scoretracker import ScoreTracker
from battle_hexes_core.scenario.scenario import ScenarioVictory
from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestScoreTracker(unittest.TestCase):
    def setUp(self):
        self.player = Player(
            name="Alice",
            type=PlayerType.HUMAN,
            factions=[Faction(id="f1", name="F1", color="#fff")],
        )

    def test_add_points_accumulates(self):
        tracker = ScoreTracker([self.player])

        tracker.add_points(self.player, 3)
        tracker.add_points(self.player, 2)

        self.assertEqual(tracker.get_score(self.player), 5)

    def test_set_score_replaces_existing_score(self):
        tracker = ScoreTracker([self.player])
        tracker.add_points(self.player, 3)

        tracker.set_score(self.player, 1)

        self.assertEqual(tracker.get_score(self.player), 1)


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

    def test_awards_points_after_combat_for_surviving_attacker(self):
        attacker = Unit(
            id="u1",
            name="Attacker",
            faction=self.faction_one,
            player=self.player_one,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        defender = Unit(
            id="u2",
            name="Defender",
            faction=self.faction_two,
            player=self.player_two,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        self.board.add_unit(attacker, 1, 1)
        self.board.add_unit(defender, 2, 1)
        game = Game([self.player_one, self.player_two], self.board)
        combat_results = CombatResults()
        combat_results.add_battle(
            CombatResultData(
                odds=(1, 1),
                die_roll=4,
                combat_result=CombatResult.DEFENDER_ELIMINATED,
                battle_participants=([attacker], [defender]),
            )
        )

        scorer = ObjectiveScorer()
        points = scorer.award_hold_objectives_after_combat(
            game, combat_results
        )

        self.assertEqual(points, 2)
        self.assertEqual(
            game.get_score_tracker().get_score(self.player_one), 2
        )

    def test_skips_attacker_retreats_after_combat(self):
        attacker = Unit(
            id="u1",
            name="Attacker",
            faction=self.faction_one,
            player=self.player_one,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        defender = Unit(
            id="u2",
            name="Defender",
            faction=self.faction_two,
            player=self.player_two,
            type="Inf",
            attack=1,
            defense=1,
            move=1,
        )
        self.board.add_unit(attacker, 1, 1)
        self.board.add_unit(defender, 2, 1)
        game = Game([self.player_one, self.player_two], self.board)
        combat_results = CombatResults()
        combat_results.add_battle(
            CombatResultData(
                odds=(1, 1),
                die_roll=1,
                combat_result=CombatResult.ATTACKER_RETREAT_2,
                battle_participants=([attacker], [defender]),
            )
        )

        scorer = ObjectiveScorer()
        points = scorer.award_hold_objectives_after_combat(
            game, combat_results
        )

        self.assertEqual(points, 0)
        self.assertEqual(
            game.get_score_tracker().get_score(self.player_one), 0
        )


class TestObjectiveControlScorer(unittest.TestCase):
    def setUp(self):
        self.board = Board(6, 6)

        self.objectives = [
            Objective(coords=(2, 1), points=1, type="occupy"),
            Objective(coords=(2, 3), points=1, type="occupy"),
            Objective(coords=(2, 5), points=1, type="occupy"),
        ]
        for objective in self.objectives:
            row, column = objective.coords
            self.board.get_hex(row, column).objectives.append(objective)

        self.airborne = Faction(id="Airborne", name="Airborne", color="#556")
        self.wehrmacht = Faction(
            id="Wehrmacht", name="Wehrmacht", color="#666"
        )
        self.airborne_player = Player(
            name="Player 1",
            type=PlayerType.HUMAN,
            factions=[self.airborne],
        )
        self.wehrmacht_player = Player(
            name="Player 2",
            type=PlayerType.CPU,
            factions=[self.wehrmacht],
        )
        self.game = Game(
            [self.airborne_player, self.wehrmacht_player],
            self.board,
        )
        self.game.victory = ScenarioVictory(
            method="objective_control",
            scoring_side="Airborne",
            description="score by occupied objectives",
        )

    def _add_unit(self, unit_id: str, faction: Faction, owner: Player, coords):
        unit = Unit(
            id=unit_id,
            name=unit_id,
            faction=faction,
            player=owner,
            type="Infantry",
            attack=1,
            defense=1,
            move=1,
        )
        row, column = coords
        self.board.add_unit(unit, row, column)

    def test_objective_control_with_mixed_occupancy(self):
        self._add_unit(
            "airborne-objective",
            self.airborne,
            self.airborne_player,
            (2, 1),
        )
        self._add_unit(
            "wehrmacht-objective",
            self.wehrmacht,
            self.wehrmacht_player,
            (2, 3),
        )

        points = ObjectiveScorer().award_hold_objectives(self.game)

        self.assertEqual(points, 1)
        self.assertEqual(self.game.get_score_tracker().get_score(
            self.airborne_player), 1)
        self.assertEqual(self.game.get_score_tracker().get_score(
            self.wehrmacht_player), 2)

    def test_objective_control_with_no_airborne_occupancy(self):
        self._add_unit(
            "wehrmacht-objective",
            self.wehrmacht,
            self.wehrmacht_player,
            (2, 3),
        )

        ObjectiveScorer().award_hold_objectives(self.game)

        self.assertEqual(self.game.get_score_tracker().get_score(
            self.airborne_player), 0)
        self.assertEqual(self.game.get_score_tracker().get_score(
            self.wehrmacht_player), 3)

    def test_objective_control_with_all_airborne_occupancy(self):
        self._add_unit("a1", self.airborne, self.airborne_player, (2, 1))
        self._add_unit("a2", self.airborne, self.airborne_player, (2, 3))
        self._add_unit("a3", self.airborne, self.airborne_player, (2, 5))

        ObjectiveScorer().award_hold_objectives(self.game)

        self.assertEqual(self.game.get_score_tracker().get_score(
            self.airborne_player), 3)
        self.assertEqual(self.game.get_score_tracker().get_score(
            self.wehrmacht_player), 0)

    def test_objective_control_recalculation_after_combat(self):
        self._add_unit("a1", self.airborne, self.airborne_player, (2, 1))
        self._add_unit(
            "w1",
            self.wehrmacht,
            self.wehrmacht_player,
            (2, 3),
        )

        combat_results = CombatResults()

        points = ObjectiveScorer().award_hold_objectives_after_combat(
            self.game, combat_results
        )

        self.assertEqual(points, 1)
        self.assertEqual(self.game.get_score_tracker().get_score(
            self.airborne_player), 1)
        self.assertEqual(self.game.get_score_tracker().get_score(
            self.wehrmacht_player), 2)

    def test_objective_control_recalculation_does_not_accumulate(self):
        scorer = ObjectiveScorer()
        self._add_unit("a1", self.airborne, self.airborne_player, (2, 1))

        scorer.award_hold_objectives(self.game)
        scorer.award_hold_objectives(self.game)

        self.assertEqual(self.game.get_score_tracker().get_score(
            self.airborne_player), 1)
        self.assertEqual(self.game.get_score_tracker().get_score(
            self.wehrmacht_player), 2)
