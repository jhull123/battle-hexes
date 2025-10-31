import unittest

from battle_hexes_api.schemas import GameModel, ScenarioModel
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.scenario.scenario import Scenario
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestScenarioModel(unittest.TestCase):
    def test_round_trip(self):
        core_scenario = Scenario(id="s1", name="Scenario 1")

        model = ScenarioModel.from_core(core_scenario)
        self.assertEqual(model.id, "s1")
        self.assertEqual(model.name, "Scenario 1")

        converted = model.to_core()
        self.assertEqual(converted, core_scenario)


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
        game = Game([player], board)

        model = GameModel.from_game(game)

        self.assertEqual(model.id, game.get_id())
        self.assertEqual(model.players, [player])
        self.assertEqual(model.board.rows, 2)
        self.assertEqual(model.board.columns, 2)
        self.assertEqual(len(model.board.units), 1)
        unit_model = model.board.units[0]
        self.assertEqual(unit_model.id, "u1")
        self.assertEqual(unit_model.row, 0)
        self.assertEqual(unit_model.column, 1)
