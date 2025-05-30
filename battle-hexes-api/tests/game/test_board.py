import unittest
import uuid
from game.board import Board
from game.sparseboard import SparseBoard
from unit.faction import Faction
from unit.unit import Unit


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)

        self.red_faction = Faction(
            id=uuid.uuid4(), name="Red Faction", color="#FF0000"
        )
        self.red_unit = Unit(
            id=uuid.uuid4(), name="Red Unit", faction=self.red_faction,
            type="Infantry", attack=2, defense=2, move=6
        )

        self.blue_faction = Faction(
            id=uuid.uuid4(), name="Blue Faction", color="#0000FF"
        )
        self.blue_unit = Unit(
            id=uuid.uuid4(), name="Blue Unit", faction=self.blue_faction,
            type="Infantry", attack=4, defense=4, move=4
        )

    def test_add_one_unit(self):
        self.board.add_unit(self.red_unit, 0, 0)

        actual_units = self.board.get_units()
        self.assertEqual(len(actual_units), 1, "Board should contain one unit")

    def test_add_out_of_bounds_row_raises_exception(self):
        with self.assertRaises(Exception):
            self.board.add_unit(self.red_unit, 6, 0)

    def test_add_out_of_bounds_col_raises_exception(self):
        with self.assertRaises(Exception):
            self.board.add_unit(self.red_unit, 1, 6)

    def test_add_unit_sets_coords(self):
        self.board.add_unit(self.red_unit, 2, 3)
        actual_units = self.board.get_units()
        self.assertEqual(actual_units[0].get_coords(), (2, 3))

    def test_update_board(self):
        self.board.add_unit(self.red_unit, 0, 4)
        self.board.add_unit(self.blue_unit, 4, 0)

        sparse_board_data = {
            "units": [
                {"id": str(self.red_unit.get_id()), "row": 2, "column": 3},
                {"id": str(self.blue_unit.get_id()), "row": 3, "column": 2},
            ]
        }
        self.board.update(SparseBoard(**sparse_board_data))

        self.assertEqual(self.red_unit.get_coords(), (2, 3))
        self.assertEqual(self.blue_unit.get_coords(), (3, 2))

    def test_get_neighboring_hexes_center_hex_even(self):
        self.board.add_unit(self.red_unit, 2, 2)

        center_hex = self.board.get_hex(2, 2)
        neighbors = self.board.get_neighboring_hexes(center_hex)

        self.assertEqual(
            len(neighbors), 6,
            "Center hex should have 6 neighbors"
        )

        expected_coords = [(1, 2), (1, 3), (2, 3), (3, 2), (2, 1), (1, 1)]
        actual_coords = [(hex.row, hex.column) for hex in neighbors]
        self.assertCountEqual(
            actual_coords, expected_coords,
            "Neighboring hexes should match expected coordinates"
        )

    def test_get_neighboring_hexes_center_hex_odd(self):
        self.board.add_unit(self.red_unit, 1, 3)

        center_hex = self.board.get_hex(1, 3)
        neighbors = self.board.get_neighboring_hexes(center_hex)

        self.assertEqual(
            len(neighbors), 6,
            "Center hex should have 6 neighbors"
        )

        expected_coords = [(0, 3), (1, 4), (2, 4), (2, 3), (2, 2), (1, 2)]
        actual_coords = [(hex.row, hex.column) for hex in neighbors]
        self.assertCountEqual(
            actual_coords, expected_coords,
            "Neighboring hexes should match expected coordinates"
        )

    def test_get_neighboring_hexes_edge_hex(self):
        self.board.add_unit(self.blue_unit, 0, 2)

        neighbors = self.board.get_neighboring_hexes(self.board.get_hex(0, 2))

        self.assertEqual(len(neighbors), 3, "Edge hex should have 3 neighbors")

        expected_coords = [(0, 3), (1, 2), (0, 1)]
        actual_coords = [(hex.row, hex.column) for hex in neighbors]
        self.assertCountEqual(
            actual_coords, expected_coords,
            "Neighboring hexes should match expected coordinates"
        )

    def test_get_neighboring_hexes_corner_hex(self):
        self.board.add_unit(self.red_unit, 0, 0)

        neighbors = self.board.get_neighboring_hexes(self.board.get_hex(0, 0))

        self.assertEqual(
            len(neighbors), 2,
            "Corner hex should have 2 neighbors"
        )

        expected_coords = [(0, 1), (1, 0)]
        actual_coords = [(hex.row, hex.column) for hex in neighbors]
        self.assertCountEqual(
            actual_coords, expected_coords,
            "Neighboring hexes should match expected coordinates"
        )
