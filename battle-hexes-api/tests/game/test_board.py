import unittest
from game.board import Board
from unit.unit import Unit

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)
        self.unit = Unit()

    def test_add_one_unit(self):
        self.board.add_unit(self.unit, 0, 0)

        actualUnits = self.board.get_units()
        self.assertEqual(len(actualUnits), 1, "Board should contain one unit")

    def test_add_out_of_bounds_row_raises_exception(self):
        with self.assertRaises(Exception):
            self.board.add_unit(self.unit, 6, 0)

    def test_add_out_of_bounds_col_raises_exception(self):
        with self.assertRaises(Exception):
            self.board.add_unit(self.unit, 1, 6)
    
    def test_add_unit_sets_coords(self):
        self.board.add_unit(self.unit, 2, 3)
        actualUnits = self.board.get_units()
        self.assertEqual(actualUnits[0].get_coords(), (2, 3))
