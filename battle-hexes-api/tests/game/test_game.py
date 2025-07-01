import unittest
from game.board import Board
from game.game import Game


class TestGame(unittest.TestCase):
    def test_game_id_is_unique(self):
        game1 = Game([], Board(5, 5))
        game2 = Game([], Board(5, 5))
        self.assertNotEqual(game1.get_id(), game2.get_id(),
                            "Game IDs should be unique")

    def test_game_board_is_initialized(self):
        board = Board(5, 5)
        game = Game([], board)
        self.assertIs(game.get_board(), board,
                      "Game board should be initialized")

    def test_next_player_cycles_through_players(self):
        # Create mock players
        class MockPlayer:
            def __init__(self, name):
                self.name = name
                self.factions = []

            def __eq__(self, other):
                return isinstance(other, MockPlayer) and \
                    self.name == other.name

        player1 = MockPlayer("Alice")
        player2 = MockPlayer("Bob")
        player3 = MockPlayer("Charlie")
        board = Board(5, 5)
        game = Game([player1, player2, player3], board)

        # Initial current player should be player1
        self.assertEqual(game.get_current_player(), player1)

        # Advance to next player
        next_player = game.next_player()
        self.assertEqual(next_player, player2)
        self.assertEqual(game.get_current_player(), player2)

        # Advance to next player
        next_player = game.next_player()
        self.assertEqual(next_player, player3)
        self.assertEqual(game.get_current_player(), player3)

        # Advance to next player (should cycle back to player1)
        next_player = game.next_player()
        self.assertEqual(next_player, player1)
        self.assertEqual(game.get_current_player(), player1)

    def test_next_player_with_no_players_returns_none(self):
        board = Board(5, 5)
        game = Game([], board)
        # next_player should return None if there are no players
        self.assertIsNone(game.next_player())
