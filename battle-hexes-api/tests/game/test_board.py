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
        print(f"Actual neighboring hexes: {actual_coords}")
        self.assertCountEqual(
            actual_coords, expected_coords,
            "Neighboring hexes should match expected coordinates"
        )

    def test_get_neighboring_hexes_center_hex_odd_3_2(self):
        self.board.add_unit(self.red_unit, 3, 2)

        center_hex = self.board.get_hex(3, 2)
        neighbors = self.board.get_neighboring_hexes(center_hex)

        self.assertEqual(
            len(neighbors), 6,
            "Center hex should have 6 neighbors"
        )

        expected_coords = [(2, 2), (2, 3), (3, 3), (4, 2), (3, 1), (2, 1)]
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

    def test_get_reachable_hexes_within_move_points(self):
        self.board.add_unit(self.red_unit, 2, 2)
        start_hex = self.board.get_hex(2, 2)

        reachable_hexes = self.board.get_reachable_hexes(
            self.red_unit, start_hex, move_points=2
        )

        actual_coords = {(hex.row, hex.column) for hex in reachable_hexes}

        # This is the full hex range for radius 2 around (2, 2)
        expected_coords = {
            (2, 2),
            (1, 2), (1, 3), (2, 3), (3, 2), (2, 1), (1, 1),
            (0, 2), (0, 3), (1, 4), (2, 4), (3, 4), (3, 3),
            (4, 2), (3, 1), (3, 0), (2, 0), (1, 0), (0, 1)
        }

        # Optional: filter expected_coords to fit your board bounds
        expected_coords = {
            (r, c) for r, c in expected_coords
            if 0 <= r < self.board.rows and 0 <= c < self.board.columns
        }

        self.assertEqual(
            len(actual_coords), len(expected_coords),
            f"Expected {len(expected_coords)} reachable hexes"
        )
        print(f"Actual reachable hexes: {actual_coords}")
        self.assertSetEqual(
            actual_coords, expected_coords,
            "Reachable hexes should match expected coordinates"
        )

    def test_get_reachable_hexes_with_no_move_points(self):
        self.board.add_unit(self.red_unit, 2, 2)
        start_hex = self.board.get_hex(2, 2)

        reachable_hexes = self.board.get_reachable_hexes(
            self.red_unit, start_hex, move_points=0
        )

        self.assertEqual(
            len(reachable_hexes), 1,
            "Unit with 0 move points should only reach its starting hex"
        )

        expected_coords = [(2, 2)]
        actual_coords = [(hex.row, hex.column) for hex in reachable_hexes]
        self.assertCountEqual(
            actual_coords, expected_coords,
            "Reachable hexes should only include the starting hex"
        )

    # def test_get_reachable_hexes_with_obstacles(self):
    #     self.board.add_unit(self.red_unit, 2, 2)
    #     self.board.add_unit(self.blue_unit, 3, 2)  # Obstacle
    #     start_hex = self.board.get_hex(2, 2)

    #     reachable_hexes = self.board.get_reachable_hexes(
    #         self.red_unit, start_hex, move_points=2
    #     )

    #     self.assertEqual(
    #         len(reachable_hexes), 6,
    #         "Unit with 2 move points should reach 6 hexes excl obstacles"
    #     )

    #     expected_coords = [
    #         (2, 2), (1, 2), (1, 3), (2, 3), (3, 3), (2, 1)
    #     ]
    #     actual_coords = [(hex.row, hex.column) for hex in reachable_hexes]
    #     self.assertCountEqual(
    #         actual_coords, expected_coords,
    #         "Reachable hexes should exclude hexes with obstacles"
    #     )
