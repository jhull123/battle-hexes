import unittest

from battle_hexes_api.schemas import (
    GameModel,
    ScenarioModel,
    SparseUnit,
    UnitModel,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.objective import Objective
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.terrain import Terrain
from battle_hexes_core.scenario.scenario import Scenario, ScenarioVictory
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestScenarioModel(unittest.TestCase):
    def test_round_trip(self):
        core_scenario = Scenario(
            id="s1",
            name="Scenario 1",
            description="Briefing text",
            victory=None,
        )

        model = ScenarioModel.from_core(core_scenario)
        self.assertEqual(model.id, "s1")
        self.assertEqual(model.name, "Scenario 1")
        self.assertEqual(model.description, "Briefing text")
        self.assertIsNone(model.victory)

        converted = model.to_core()
        self.assertEqual(converted, core_scenario)

    def test_round_trip_with_victory(self):
        core_scenario = Scenario(
            id="s2",
            name="Scenario 2",
            description="Hold crossroads.",
            victory=ScenarioVictory(
                method="objective_control",
                scoring_side="Allies",
                description="Allies win by holding the objective.",
            ),
        )

        model = ScenarioModel.from_core(core_scenario)

        self.assertEqual(model.victory.method, "objective_control")
        self.assertEqual(model.victory.scoring_side, "Allies")
        self.assertEqual(
            model.victory.description,
            "Allies win by holding the objective.",
        )

        converted = model.to_core()
        self.assertEqual(converted.id, "s2")
        self.assertEqual(converted.name, "Scenario 2")
        self.assertEqual(converted.description, "Hold crossroads.")
        self.assertEqual(converted.victory.method, "objective_control")
        self.assertEqual(converted.victory.scoring_side, "Allies")
        self.assertEqual(
            converted.victory.description,
            "Allies win by holding the objective.",
        )


class TestGameModel(unittest.TestCase):
    def test_from_game(self):
        board = Board(2, 2)
        faction = Faction(id="f1", name="Faction 1", color="#ffffff")
        player = Player(
            name="Alice",
            type=PlayerType.HUMAN,
            factions=[faction],
        )
        unit = Unit(
            id="u1",
            name="Unit 1",
            faction=faction,
            player=player,
            type="Infantry",
            attack=3,
            defense=2,
            move=1,
        )
        board.add_unit(unit, 0, 1)
        board.set_road_types({"secondary": 1.0})
        board.set_road_paths((("secondary", ((0, 0), (0, 1))),))
        board.get_hex(0, 0).set_terrain(Terrain("open", "#C6AA5C"))
        board.get_hex(0, 0).objectives.append(
            Objective(coords=(0, 0), points=2, type="hold")
        )
        game = Game([player], board)
        scenario = Scenario(
            id="scenario-1",
            name="Scenario 1",
            terrain_default="open",
        )

        model = GameModel.from_game(game, scenario)

        self.assertEqual(model.id, game.get_id())
        self.assertEqual(model.players, [player])
        self.assertEqual(model.board.rows, 2)
        self.assertEqual(model.board.columns, 2)
        self.assertEqual(len(model.board.units), 1)
        self.assertEqual(model.board.terrain.default, "open")
        self.assertEqual(model.board.road_types, {"secondary": 1.0})
        self.assertEqual(model.board.road_paths[0].type, "secondary")
        self.assertEqual(
            [
                (coord.row, coord.column)
                for coord in model.board.road_paths[0].path
            ],
            [(0, 0), (0, 1)],
        )
        self.assertEqual(len(model.objectives), 1)
        objective_model = model.objectives[0]
        self.assertEqual(objective_model.row, 0)
        self.assertEqual(objective_model.column, 0)
        self.assertEqual(objective_model.points, 2)
        self.assertEqual(objective_model.type, "hold")
        unit_model = model.board.units[0]
        self.assertEqual(unit_model.id, "u1")
        self.assertEqual(unit_model.row, 0)
        self.assertEqual(unit_model.column, 1)


class TestSparseUnit(unittest.TestCase):
    def test_from_unit(self):
        faction = Faction(id="f2", name="Faction 2", color="#000000")
        player = Player(
            name="Bob",
            type=PlayerType.HUMAN,
            factions=[faction],
        )
        unit = Unit(
            id="u2",
            name="Unit 2",
            faction=faction,
            player=player,
            type="Infantry",
            attack=4,
            defense=3,
            move=2,
            row=5,
            column=7,
        )

        sparse_unit = SparseUnit.from_unit(unit)

        self.assertEqual(sparse_unit.id, "u2")
        self.assertEqual(sparse_unit.row, 5)
        self.assertEqual(sparse_unit.column, 7)
        self.assertTrue(sparse_unit.defensive_fire_available)


class TestUnitModel(unittest.TestCase):
    def test_from_unit(self):
        faction = Faction(id="f3", name="Faction 3", color="#ff0000")
        player = Player(
            name="Charlie",
            type=PlayerType.HUMAN,
            factions=[faction],
        )
        unit = Unit(
            id="u3",
            name="Unit 3",
            faction=faction,
            player=player,
            type="Cavalry",
            attack=6,
            defense=4,
            echelon="company",
            move=3,
            row=2,
            column=4,
        )

        unit_model = UnitModel.from_unit(unit)

        self.assertEqual(unit_model.id, "u3")
        self.assertEqual(unit_model.name, "Unit 3")
        self.assertEqual(unit_model.faction_id, "f3")
        self.assertEqual(unit_model.type, "Cavalry")
        self.assertEqual(unit_model.attack, 6)
        self.assertEqual(unit_model.echelon, "company")
        self.assertEqual(unit_model.defense, 4)
        self.assertEqual(unit_model.move, 3)
        self.assertEqual(unit_model.row, 2)
        self.assertEqual(unit_model.column, 4)
        self.assertTrue(unit_model.defensive_fire_available)
