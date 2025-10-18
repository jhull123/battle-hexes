"""Unit tests for the GameCreator class."""
import unittest
from unittest.mock import Mock

from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario import Scenario, ScenarioFaction
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
        mock_scenario.board_size = (10, 20)
        mock_scenario.factions = ()
        mock_scenario.units = ()

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
        mock_scenario.board_size = (8, 8)
        mock_scenario.factions = ()
        mock_scenario.units = ()
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

        self.creator.assign_factions(scenario, player1, player2)

        self.assertEqual(len(player1.factions), 1)
        self.assertEqual(len(player2.factions), 1)
        self.assertEqual(player1.factions[0].id, "faction-1")
        self.assertEqual(player2.factions[0].id, "faction-2")

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
