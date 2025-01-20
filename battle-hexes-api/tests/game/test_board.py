import unittest
import uuid
from game.board import Board
from game.sparseboard import SparseBoard
from unit.faction import Faction
from unit.unit import Unit


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)

        self.red_faction = Faction(id=uuid.uuid4(), name="Red Faction",
                                   color="#FF0000")
        self.red_unit = Unit(id=uuid.uuid4(), name="Red Unit",
                             faction=self.red_faction,
                             type="Infantry",
                             attack=2, defense=2, move=6)

        self.blue_faction = Faction(id=uuid.uuid4(), name="Blue Faction",
                                    color="#0000FF")
        self.blue_unit = Unit(id=uuid.uuid4(), name="Blue Unit",
                              faction=self.blue_faction,
                              type="Infantry",
                              attack=4, defense=4, move=4)

    def test_add_one_unit(self):
        self.board.add_unit(self.red_unit, 0, 0)

        actualUnits = self.board.get_units()
        self.assertEqual(len(actualUnits), 1, "Board should contain one unit")

    def test_add_out_of_bounds_row_raises_exception(self):
        with self.assertRaises(Exception):
            self.board.add_unit(self.red_unit, 6, 0)

    def test_add_out_of_bounds_col_raises_exception(self):
        with self.assertRaises(Exception):
            self.board.add_unit(self.red_unit, 1, 6)

    def test_add_unit_sets_coords(self):
        self.board.add_unit(self.red_unit, 2, 3)
        actualUnits = self.board.get_units()
        self.assertEqual(actualUnits[0].get_coords(), (2, 3))

    def test_update_board(self):
        self.board.add_unit(self.red_unit, 0, 4)
        self.board.add_unit(self.blue_unit, 4, 0)

        sparse_board_data = {
            "units": [
                {"id": str(self.red_unit.get_id()), "row": 2, "column": 3},
                {"id": str(self.blue_unit.get_id()), "row": 3, "column": 2}
            ]
        }
        self.board.update(SparseBoard(**sparse_board_data))

        self.assertEqual(self.red_unit.get_coords(), (2, 3))
        self.assertEqual(self.blue_unit.get_coords(), (3, 2))
