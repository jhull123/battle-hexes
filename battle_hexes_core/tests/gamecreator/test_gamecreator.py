"""Unit tests for the GameCreator class."""
import unittest
from unittest.mock import Mock, patch

from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario import (
    Scenario,
    ScenarioFaction,
    ScenarioHexData,
    ScenarioTerrainType,
    ScenarioUnit,
)
from battle_hexes_core.game.player import Player, PlayerType


class TestGameCreator(unittest.TestCase):
    """Test cases for the GameCreator class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.creator = GameCreator()

    def test_game_board_size_matches_scenario(self):
        """Test that created game's board size matches the scenario spec."""
        # Set up mock scenario with specific board size
        mock_scenario = Mock(spec=Scenario)
        mock_scenario.id = "s1"
        mock_scenario.board_size = (10, 20)
        mock_scenario.factions = ()
        mock_scenario.units = ()
        mock_scenario.terrain_default = None
        mock_scenario.terrain_types = {}
        mock_scenario.hex_data = ()

        # Set up mock players
        mock_player1 = Mock(spec=Player)
        mock_player2 = Mock(spec=Player)

        # Create game using GameCreator
        game = self.creator.create_game(
            scenario=mock_scenario,
            player1=mock_player1,
            player2=mock_player2
        )

        # Verify board dimensions
        self.assertEqual(game.board.rows, 10)
        self.assertEqual(game.board.columns, 20)

    def test_players_set_correctly_in_game(self):
        """Test that players are correctly set in the created game."""
        # Set up test fixtures
        mock_scenario = Mock(spec=Scenario)
        mock_scenario.id = "s1"
        mock_scenario.board_size = (8, 8)
        mock_scenario.factions = ()
        mock_scenario.units = ()
        mock_scenario.terrain_default = None
        mock_scenario.terrain_types = {}
        mock_scenario.hex_data = ()
        mock_player1 = Mock(spec=Player)
        mock_player2 = Mock(spec=Player)

        # Create game using GameCreator
        game = self.creator.create_game(
            scenario=mock_scenario,
            player1=mock_player1,
            player2=mock_player2
        )

        # Verify players list contains both players in correct order
        self.assertEqual(len(game.players), 2)
        self.assertEqual(game.players[0], mock_player1)
        self.assertEqual(game.players[1], mock_player2)

        # Verify first player is set as current player
        self.assertEqual(game.current_player, mock_player1)

    def test_assign_factions_adds_factions_to_players(self):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario",
            factions=(
                ScenarioFaction(
                    id="faction-1",
                    name="Faction One",
                    color="#FF0000",
                    player="Player 1",
                ),
                ScenarioFaction(
                    id="faction-2",
                    name="Faction Two",
                    color="#0000FF",
                    player="Player 2",
                ),
            ),
        )

        player1 = Player(name="Player 1", type=PlayerType.HUMAN, factions=[])
        player2 = Player(name="Player 2", type=PlayerType.CPU, factions=[])

        faction_by_id, player_by_faction_id = self.creator.assign_factions(
            scenario,
            player1,
            player2,
        )

        self.assertEqual(len(player1.factions), 1)
        self.assertEqual(len(player2.factions), 1)
        self.assertEqual(player1.factions[0].id, "faction-1")
        self.assertEqual(player2.factions[0].id, "faction-2")
        self.assertIn("faction-1", faction_by_id)
        self.assertIn("faction-2", faction_by_id)
        self.assertIs(faction_by_id["faction-1"], player1.factions[0])
        self.assertIs(player_by_faction_id["faction-1"], player1)

    def test_assign_factions_raises_for_unknown_player(self):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario",
            factions=(
                ScenarioFaction(
                    id="faction-1",
                    name="Faction One",
                    color="#FF0000",
                    player="Player 3",
                ),
            ),
        )

        player1 = Player(name="Player 1", type=PlayerType.HUMAN, factions=[])
        player2 = Player(name="Player 2", type=PlayerType.CPU, factions=[])

        with self.assertRaises(NameError):
            self.creator.assign_factions(scenario, player1, player2)

    def test_add_units_creates_units_on_board(self):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario",
            board_size=(5, 5),
            factions=(
                ScenarioFaction(
                    id="faction-1",
                    name="Faction One",
                    color="#FF0000",
                    player="Player 1",
                ),
            ),
            units=(
                ScenarioUnit(
                    id="unit-1",
                    name="Infantry",
                    faction="faction-1",
                    type="Infantry",
                    attack=3,
                    defense=2,
                    movement=5,
                ),
            ),
            hex_data=(
                ScenarioHexData(
                    coords=(1, 2),
                    units=("unit-1",),
                ),
            ),
        )

        player1 = Player(name="Player 1", type=PlayerType.HUMAN, factions=[])
        player2 = Player(name="Player 2", type=PlayerType.CPU, factions=[])

        game = self.creator.create_game(scenario, player1, player2)
        board_units = game.board.get_units()

        self.assertEqual(len(board_units), 1)
        unit = board_units[0]
        self.assertEqual(unit.get_id(), "unit-1")
        self.assertEqual(unit.get_name(), "Infantry")
        self.assertEqual(unit.get_coords(), (1, 2))
        self.assertIs(unit.player, player1)
        self.assertEqual(player1.factions[0].id, unit.get_faction().id)

    def test_add_units_raises_for_unknown_faction(self):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario",
            board_size=(5, 5),
            factions=(
                ScenarioFaction(
                    id="faction-1",
                    name="Faction One",
                    color="#FF0000",
                    player="Player 1",
                ),
            ),
            units=(
                ScenarioUnit(
                    id="unit-1",
                    name="Infantry",
                    faction="unknown-faction",
                    type="Infantry",
                    attack=3,
                    defense=2,
                    movement=5
                ),
            ),
            hex_data=(
                ScenarioHexData(
                    coords=(0, 0),
                    units=("unit-1",),
                ),
            ),
        )

        player1 = Player(name="Player 1", type=PlayerType.HUMAN, factions=[])
        player2 = Player(name="Player 2", type=PlayerType.CPU, factions=[])

        with self.assertRaises(NameError):
            self.creator.create_game(scenario, player1, player2)

    def test_add_terrain_populates_board_hexes(self):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario",
            board_size=(2, 2),
            terrain_default="open",
            terrain_types={
                "open": ScenarioTerrainType(color="#C6AA5C"),
                "village": ScenarioTerrainType(color="#9A8F7A"),
            },
            hex_data=(
                ScenarioHexData(
                    coords=(1, 1),
                    terrain="village",
                ),
            ),
        )

        player1 = Player(name="Player 1", type=PlayerType.HUMAN, factions=[])
        player2 = Player(name="Player 2", type=PlayerType.CPU, factions=[])

        game = self.creator.create_game(scenario, player1, player2)

        default_hex = game.board.get_hex(0, 0)
        override_hex = game.board.get_hex(1, 1)

        self.assertIsNotNone(default_hex)
        self.assertIsNotNone(override_hex)
        self.assertEqual(default_hex.terrain.name, "open")
        self.assertEqual(default_hex.terrain.hex_color, "#C6AA5C")
        self.assertEqual(override_hex.terrain.name, "village")
        self.assertEqual(override_hex.terrain.hex_color, "#9A8F7A")

    @patch("battle_hexes_core.gamecreator.gamecreator.load_scenario")
    def test_build_game_components_from_scenario_id(self, mock_load_scenario):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario",
            board_size=(3, 3),
            factions=(
                ScenarioFaction(
                    id="faction-1",
                    name="Faction One",
                    color="#FF0000",
                    player="Player 1",
                ),
                ScenarioFaction(
                    id="faction-2",
                    name="Faction Two",
                    color="#0000FF",
                    player="Player 2",
                ),
            ),
            units=(
                ScenarioUnit(
                    id="unit-1",
                    name="Infantry",
                    faction="faction-1",
                    type="Infantry",
                    attack=3,
                    defense=2,
                    movement=5
                ),
                ScenarioUnit(
                    id="unit-2",
                    name="Scout",
                    faction="faction-2",
                    type="Scout",
                    attack=2,
                    defense=1,
                    movement=6
                ),
            ),
            hex_data=(
                ScenarioHexData(
                    coords=(0, 0),
                    units=("unit-1",),
                ),
                ScenarioHexData(
                    coords=(1, 2),
                    units=("unit-2",),
                ),
            ),
        )
        mock_load_scenario.return_value = scenario

        player1 = Player(name="Alpha", type=PlayerType.HUMAN, factions=[])
        player2 = Player(name="Beta", type=PlayerType.CPU, factions=[])

        result = self.creator.build_game_components(
            "scenario-1",
            (player1, player2),
        )
        scenario_result, players, units, game = result

        mock_load_scenario.assert_called_once_with("scenario-1")
        self.assertIs(scenario_result, scenario)
        self.assertEqual(players[0], player1)
        self.assertEqual(players[1], player2)
        self.assertEqual(len(player1.factions), 1)
        self.assertEqual(len(player2.factions), 1)
        unit_ids = {unit.get_id() for unit in units}
        self.assertEqual(unit_ids, {"unit-1", "unit-2"})
        self.assertEqual(game.board.get_rows(), 3)
        self.assertEqual(game.board.get_columns(), 3)
        self.assertEqual(game.scenario_id, "scenario-1")
        self.assertEqual(
            game.player_type_ids,
            (type(player1).__name__, type(player2).__name__),
        )

    def test_build_game_components_requires_two_players(self):
        scenario = Scenario(
            id="scenario-1",
            name="Scenario",
            board_size=(3, 3),
            factions=(),
            units=(),
        )

        player = Player(name="Solo", type=PlayerType.HUMAN, factions=[])

        with self.assertRaises(ValueError):
            self.creator.build_game_components(scenario, (player,))
