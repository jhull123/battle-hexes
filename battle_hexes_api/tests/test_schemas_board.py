import unittest

from battle_hexes_api.schemas import (
    BoardModel,
    SparseBoard,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.terrain import Terrain
from battle_hexes_core.scenario.scenario import Scenario, ScenarioTerrainType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestSparseBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)
        self.red_faction = Faction(
            id="f1",
            name="Red Faction",
            color="#FF0000"
        )
        self.red_player = Player(
            name='Red Player',
            type=PlayerType.HUMAN,
            factions=[self.red_faction]
        )
        self.red_unit = Unit(
            id="u1",
            name="Red Unit",
            faction=self.red_faction,
            player=self.red_player,
            type="Infantry",
            attack=2,
            defense=2,
            move=6
        )
        self.blue_faction = Faction(
            id="f2",
            name="Blue Faction",
            color="#0000FF"
        )
        self.blue_player = Player(
            name='Blue Player',
            type=PlayerType.CPU,
            factions=[self.blue_faction]
        )
        self.blue_unit = Unit(
            id="u2",
            name="Blue Unit",
            faction=self.blue_faction,
            player=self.blue_player,
            type="Infantry",
            attack=4,
            defense=4,
            move=4
        )

    def test_update_board(self):
        # Set up initial unit positions
        self.board.add_unit(self.red_unit, 0, 4)
        self.board.add_unit(self.blue_unit, 4, 0)

        # Create sparse board data for moving units
        sparse_board_data = {
            "units": [
                {
                    "id": str(self.red_unit.get_id()),
                    "row": 2,
                    "column": 3
                },
                {
                    "id": str(self.blue_unit.get_id()),
                    "row": 3,
                    "column": 2
                },
            ]
        }

        # Apply the sparse board updates
        SparseBoard(**sparse_board_data).apply_to_board(self.board)

        # Verify unit positions were updated
        self.assertEqual(self.red_unit.get_coords(), (2, 3))
        self.assertEqual(self.blue_unit.get_coords(), (3, 2))


class TestBoardModel(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)
        self.red_faction = Faction(
            id="f1",
            name="Red Faction",
            color="#FF0000"
        )
        self.red_player = Player(
            name='Red Player',
            type=PlayerType.HUMAN,
            factions=[self.red_faction]
        )
        self.red_unit = Unit(
            id="u1",
            name="Red Unit",
            faction=self.red_faction,
            player=self.red_player,
            type="Infantry",
            attack=2,
            defense=2,
            move=6
        )

    def test_to_board_model_returns_schema(self):
        self.board.add_unit(self.red_unit, 0, 0)

        board_model = BoardModel.from_board(self.board)

        self.assertIsInstance(board_model, BoardModel)
        self.assertEqual(board_model.rows, self.board.get_rows())
        self.assertEqual(board_model.columns, self.board.get_columns())

    def test_to_board_model_includes_terrain_summary(self):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario 1",
            terrain_default="open",
            terrain_types={
                "open": ScenarioTerrainType(color="#C6AA5C"),
                "village": ScenarioTerrainType(color="#9A8F7A", move_cost=2),
            },
        )
        self.board.get_hex(0, 0).set_terrain(Terrain("open", "#C6AA5C"))
        self.board.get_hex(1, 1).set_terrain(Terrain("village", "#9A8F7A"))

        board_model = BoardModel.from_board(self.board, scenario)

        self.assertEqual(board_model.terrain.default, "open")
        self.assertEqual(board_model.terrain.types["open"].color, "#C6AA5C")
        self.assertEqual(board_model.terrain.types["open"].move_cost, 1)
        self.assertEqual(
            board_model.terrain.types["village"].color, "#9A8F7A"
        )
        self.assertEqual(board_model.terrain.types["village"].move_cost, 2)
        self.assertEqual(len(board_model.terrain.hexes), 1)
        self.assertEqual(board_model.terrain.hexes[0].row, 1)
        self.assertEqual(board_model.terrain.hexes[0].column, 1)
        self.assertEqual(board_model.terrain.hexes[0].terrain, "village")

    def test_to_board_model_includes_road_metadata(self):
        self.board.set_road_types({"secondary": 1.0})
        self.board.set_road_paths(
            (("secondary", ((1, 1), (1, 2), (2, 2))),)
        )

        board_model = BoardModel.from_board(self.board)

        self.assertEqual(board_model.road_types, {"secondary": 1.0})
        self.assertEqual(len(board_model.road_paths), 1)
        self.assertEqual(board_model.road_paths[0].type, "secondary")
        self.assertEqual(
            [
                (coord.row, coord.column)
                for coord in board_model.road_paths[0].path
            ],
            [(1, 1), (1, 2), (2, 2)],
        )
