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
        game_id = "game-123"
        mock_game = MagicMock()
        mock_game.id = game_id
        mock_game_repo.get_game.return_value = mock_game
        sparse_board_data = {
            "units": []
        }

        self.client.post(
            f"/combat/{game_id}", json=sparse_board_data)

        mock_game.update.assert_called_once_with(
            SparseBoard(**sparse_board_data))
        mock_game.resolve_combat.assert_called_once()
        mock_game.get_sparse_board.assert_called_once()
