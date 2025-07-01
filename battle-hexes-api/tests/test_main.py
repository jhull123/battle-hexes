import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from src.game.sparseboard import SparseBoard


class TestFastAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_game(self):
        post_response = self.client.post('/games')
        new_game_id = post_response.json().get('id')

        get_response = self.client.get(f'/games/{new_game_id}')
        self.assertEqual(new_game_id, get_response.json().get('id'))

    @patch('main.game_repo')
    def test_resolve_combat_placeholder(self, mock_game_repo):
        mock_board = MagicMock()
        sparse_board_data = {
            "units": []
        }

        game_id = "game-123"
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game_repo.get_game.return_value = mock_game
        mock_game.get_board.return_value = mock_board

        self.client.post(
            f"/games/{game_id}/combat", json=sparse_board_data)

        mock_game.update.assert_called_once_with(
            SparseBoard(**sparse_board_data))
        mock_game_repo.update_game.assert_called_once_with(mock_game)
        mock_board.to_sparse_board.assert_called_once()

    @patch('main.game_repo')
    def test_generate_movement(self, mock_game_repo):
        mock_plan = MagicMock()
        mock_player = MagicMock()
        mock_player.movement.return_value = [mock_plan]
        mock_game = MagicMock()
        mock_game.get_current_player.return_value = mock_player
        mock_game_repo.get_game.return_value = mock_game
        mock_plan.to_dict.return_value = {"plan": 1}

        game_id = "game-456"
        response = self.client.post(f"/games/{game_id}/movement")

        self.assertEqual(response.json(), {"plans": [{"plan": 1}]})
        mock_player.movement.assert_called_once_with()
        mock_plan.to_dict.assert_called_once_with()

    @patch('main.game_repo')
    def test_end_turn(self, mock_game_repo):
        mock_game = MagicMock()
        mock_game_repo.get_game.return_value = mock_game
        sparse_board_data = {"units": []}

        game_id = "game-789"
        self.client.post(f"/games/{game_id}/end-turn", json=sparse_board_data)

        mock_game.update.assert_called_once_with(
            SparseBoard(**sparse_board_data))
        mock_game.next_player.assert_called_once_with()
        mock_game_repo.update_game.assert_called_once_with(mock_game)
