import unittest
import uuid
from src.game.board import Board
from src.game.game import Game
from src.game.game import Player, PlayerType
from src.combat.combat import Combat
from src.combat.combatresult import CombatResult
from src.unit.faction import Faction
from src.unit.unit import Unit


class TestCombat(unittest.TestCase):
    def setUp(self):
        self.red_faction = Faction(id=uuid.uuid4(), name='Red', color='red')
        self.blue_faction = Faction(id=uuid.uuid4(), name='Blue', color='blue')

        self.red_player = Player(
            name='Red Player',
            type=PlayerType.HUMAN,
            factions=[self.red_faction]
        )
        self.blue_player = Player(
            name='Blue Player',
            type=PlayerType.CPU,
            factions=[self.blue_faction]
        )

        self.board = Board(10, 10)
        self.game = Game([self.red_player, self.blue_player], self.board)
        self.combat = Combat(self.game)

        self.red_unit = Unit(id=uuid.uuid4(), name='Red Unit',
                             faction=self.red_faction, type='Infantry',
                             attack=4, defense=4, move=4)
        self.blue_unit = Unit(id=uuid.uuid4(), name='Blue Unit',
                              faction=self.blue_faction, type='Recon',
                              attack=2, defense=2, move=6)

    def test_results_empty_when_empty_board(self):
        combat_result = self.combat.resolve_combat()
        self.assertEqual(0, len(combat_result.get_battles()))

    def test_results_empty_when_no_combat(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 3, 5)
        combat_result = self.combat.resolve_combat()
        self.assertEqual(0, len(combat_result.get_battles()))

    def test_board_is_unchanged_when_no_combat(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 3, 5)

        self.combat.resolve_combat()

        self.assertEqual((6, 4), self.red_unit.get_coords())
        self.assertEqual((3, 5), self.blue_unit.get_coords())

    def test_board_one_battle(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 6, 5)
        self.combat.set_static_die_roll(6)

        combat_results = self.combat.resolve_combat()
        battles = combat_results.get_battles()

        self.assertEqual(1, len(battles))

    def test_board_attacker_elim_leaves_one_unit_on_the_board(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 6, 5)
        self.combat.set_static_die_roll(6)

        self.combat.resolve_combat()

        self.assertEqual(1, len(self.board.get_units()))

    def test_board_attacker_elim_has_correct_combat_data(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 6, 5)
        self.combat.set_static_die_roll(6)

        combat_result = self.combat.resolve_combat().get_battles()[0]

        self.assertEqual((2, 1), combat_result.get_odds())
        self.assertEqual(6, combat_result.get_die_roll())
        self.assertEqual(
            CombatResult.ATTACKER_ELIMINATED,
            combat_result.get_combat_result()
        )
