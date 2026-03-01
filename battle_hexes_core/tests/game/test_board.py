import unittest
import uuid
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.objective import Objective
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.terrain import Terrain
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)

        self.red_faction = Faction(
            id=str(uuid.uuid4()), name="Red Faction", color="#FF0000"
        )
        self.red_player = Player(
            name='Red Player',
            type=PlayerType.HUMAN,
            factions=[self.red_faction]
        )
        self.red_unit = Unit(
            id=str(uuid.uuid4()), name="Red Unit", faction=self.red_faction,
            player=self.red_player,
            type="Infantry", attack=2, defense=2, move=6
        )

        self.blue_faction = Faction(
            id=str(uuid.uuid4()), name="Blue Faction", color="#0000FF"
        )
        self.blue_player = Player(
            name='Blue Player',
            type=PlayerType.CPU,
            factions=[self.blue_faction]
        )
        self.blue_unit = Unit(
            id=str(uuid.uuid4()), name="Blue Unit",
            faction=self.blue_faction,
            player=self.blue_player,
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

    def test_set_and_get_road_types(self):
        road_types = {"highway": 0.5, "secondary": 1.0}

        self.board.set_road_types(road_types)
        fetched = self.board.get_road_types()

        self.assertEqual(fetched, road_types)
        self.assertIsNot(fetched, road_types)

    def test_set_and_get_road_paths(self):
        road_paths = (
            ("highway", ((0, 0), (0, 1), (0, 2))),
            ("secondary", ((2, 1), (2, 2))),
        )

        self.board.set_road_paths(road_paths)

        self.assertEqual(self.board.get_road_paths(), road_paths)

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

    def test_get_objectives(self):
        objective_one = Objective(coords=(0, 1), points=1, type="hold")
        objective_two = Objective(coords=(2, 3), points=3, type="hold")
        self.board.get_hex(0, 1).objectives.append(objective_one)
        self.board.get_hex(2, 3).objectives.append(objective_two)

        objectives = self.board.get_objectives()

        self.assertCountEqual(objectives, [objective_one, objective_two])

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

    def test_enemy_adjacent_no_enemies(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.red_unit, 1, 2)  # Friendly unit

        target_hex = self.board.get_hex(2, 2)
        self.assertFalse(
            self.board.enemy_adjacent(self.red_unit, target_hex),
            "Hex should not be adjacent to any enemy units"
        )

    def test_enemy_adjacent_one_enemy(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.blue_unit, 1, 2)  # Enemy unit

        target_hex = self.board.get_hex(2, 2)
        self.assertTrue(
            self.board.enemy_adjacent(self.red_unit, target_hex),
            "Hex should be adjacent to an enemy unit"
        )

    def test_enemy_adjacent_multiple_enemies(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.blue_unit, 1, 2)  # Enemy unit
        self.board.add_unit(self.blue_unit, 2, 3)  # Another enemy unit

        target_hex = self.board.get_hex(2, 2)
        self.assertTrue(
            self.board.enemy_adjacent(self.red_unit, target_hex),
            "Hex should be adjacent to multiple enemy units"
        )

    def test_enemy_adjacent_all_friendly(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.red_unit, 1, 2)  # Friendly unit
        self.board.add_unit(self.red_unit, 2, 3)  # Another friendly unit

        target_hex = self.board.get_hex(2, 2)
        self.assertFalse(
            self.board.enemy_adjacent(self.red_unit, target_hex),
            "Hex should not be adjacent to any enemy units"
        )

    def test_enemy_adjacent_no_neighbors(self):
        self.board.add_unit(self.red_unit, 0, 0)  # Corner hex

        target_hex = self.board.get_hex(0, 0)
        self.assertFalse(
            self.board.enemy_adjacent(self.red_unit, target_hex),
            "Hex with no neighbors should not be adjacent to any enemy units"
        )

    def test_get_reachable_hexes_with_obstacles(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.blue_unit, 3, 3)  # Obstacle
        start_hex = self.board.get_hex(2, 2)

        reachable_hexes = self.board.get_reachable_hexes(
            self.red_unit, start_hex, move_points=2
        )

        self.assertEqual(
            len(reachable_hexes), 16,
            "Unit with 2 move points should reach 16 hexes excl obstacles"
        )

    def test_shortest_path_avoids_enemy_adjacent(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.blue_unit, 0, 3)

        start_hex = self.board.get_hex(2, 2)
        end_hex = self.board.get_hex(0, 2)

        path = self.board.shortest_path(self.red_unit, start_hex, end_hex)
        coords = [(h.row, h.column) for h in path]

        self.assertTrue(len(coords) > 1)
        self.assertNotIn((1, 2), coords)
        self.assertEqual(coords[-1], (0, 2))

    def test_shortest_path_blocked_when_start_adjacent(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.blue_unit, 1, 2)

        start_hex = self.board.get_hex(2, 2)
        end_hex = self.board.get_hex(2, 3)

        path = self.board.shortest_path(self.red_unit, start_hex, end_hex)
        self.assertEqual(path, [])

    def test_get_reachable_hexes_respects_terrain_move_cost(self):
        self.board.add_unit(self.red_unit, 2, 2)
        start_hex = self.board.get_hex(2, 2)

        mountain = Terrain("mountain", "#777777", move_cost=3)
        forest = Terrain("forest", "#558855", move_cost=2)
        self.board.get_hex(2, 3).set_terrain(mountain)
        self.board.get_hex(3, 2).set_terrain(forest)

        reachable_hexes = self.board.get_reachable_hexes(
            self.red_unit, start_hex, move_points=2
        )
        actual_coords = {(hex.row, hex.column) for hex in reachable_hexes}

        self.assertNotIn((2, 3), actual_coords)
        self.assertIn((3, 2), actual_coords)

    def test_shortest_path_prefers_lower_total_cost(self):
        self.board = Board(3, 4)
        self.board.add_unit(self.red_unit, 1, 0)
        start_hex = self.board.get_hex(1, 0)
        end_hex = self.board.get_hex(1, 3)

        swamp = Terrain("swamp", "#445533", move_cost=4)
        self.board.get_hex(1, 1).set_terrain(swamp)

        path = self.board.shortest_path(self.red_unit, start_hex, end_hex)
        coords = [(h.row, h.column) for h in path]

        self.assertEqual(coords[0], (1, 0))
        self.assertEqual(coords[-1], (1, 3))
        self.assertNotIn((1, 1), coords)

    def test_reachable_hexes_stop_expanding_when_start_enemy_adjacent(self):
        self.board.add_unit(self.red_unit, 2, 2)
        self.board.add_unit(self.blue_unit, 1, 2)
        start_hex = self.board.get_hex(2, 2)

        reachable_hexes = self.board.get_reachable_hexes(
            self.red_unit, start_hex, move_points=3
        )
        coords = {(h.row, h.column) for h in reachable_hexes}

        self.assertEqual(coords, {(2, 2)})

    def test_hex_distance(self):
        a = self.board.get_hex(0, 0)
        b = self.board.get_hex(1, 0)
        c = self.board.get_hex(1, 1)

        self.assertEqual(Board.hex_distance(a, a), 0)
        self.assertEqual(Board.hex_distance(a, b), 1)
        self.assertEqual(Board.hex_distance(a, c), 2)

    def test_path_towards_limited_steps(self):
        self.board.add_unit(self.red_unit, 2, 1)
        self.board.add_unit(self.blue_unit, 4, 1)

        enemy_hex = self.board.get_hex(4, 1)
        path = self.board.path_towards(self.red_unit, enemy_hex, 1)
        coords = [(h.row, h.column) for h in path]
        self.assertEqual(coords, [(2, 1), (3, 1)])

    def test_path_towards_prefers_shortest_adjacent_path(self):
        self.board.add_unit(self.red_unit, 0, 0)
        self.board.add_unit(self.blue_unit, 1, 2)

        enemy_hex = self.board.get_hex(1, 2)
        path = self.board.path_towards(
            self.red_unit, enemy_hex, self.red_unit.get_move()
        )
        coords = [(h.row, h.column) for h in path]

        self.assertEqual(coords, [(0, 0), (0, 1)])

    def test_path_away_from_increases_distance(self):
        self.board.add_unit(self.red_unit, 2, 1)
        self.board.add_unit(self.blue_unit, 0, 1)

        threat_hex = self.board.get_hex(0, 1)
        start_hex = self.board.get_hex(2, 1)
        start_dist = Board.hex_distance(start_hex, threat_hex)
        path = self.board.path_away_from(self.red_unit, threat_hex, 1)
        end_hex = path[-1]
        end_dist = Board.hex_distance(end_hex, threat_hex)
        self.assertEqual(len(path), 2)
        self.assertGreater(end_dist, start_dist)
