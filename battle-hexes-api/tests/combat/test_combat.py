import unittest
import uuid
from game.board import Board
from combat.combat import Combat
from unit.faction import Faction
from unit.unit import Unit


class TestCombat(unittest.TestCase):
    def setUp(self):
        self.board = Board(10, 10)
        self.combat = Combat(self.board)

        self.red_faction = Faction(id=uuid.uuid4(), name='Red', color='red')
        self.red_unit = Unit(id=uuid.uuid4(), name='Red Unit',
                             faction=self.red_faction, type='Infantry',
                             attack=2, defense=2, move=6)

        self.blue_faction = Faction(id=uuid.uuid4(), name='Blue', color='blue')
        self.blue_unit = Unit(id=uuid.uuid4(), name='Blue Unit',
                              faction=self.blue_faction, type='Infantry',
                              attack=4, defense=4, move=6)

    def test_results_empty_when_empty_board(self):
        combat_result = self.combat.resolve_combat()
        self.assertEqual(len(combat_result.get_battles()), 0)

    def test_results_empty_when_no_combat(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 3, 5)
        combat_result = self.combat.resolve_combat()
        self.assertEqual(len(combat_result.get_battles()), 0)

    def test_board_is_unchanged_when_no_combat(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 3, 5)

        self.combat.resolve_combat()

        self.assertEqual(self.red_unit.get_coords(), (6, 4))
        self.assertEqual(self.blue_unit.get_coords(), (3, 5))
