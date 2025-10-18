"""Unit tests for the GameCreator class."""
import unittest
from unittest.mock import Mock

from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario import Scenario
from battle_hexes_core.game.player import Player


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
