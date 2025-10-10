import unittest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from battle_hexes_api.main import app
from battle_hexes_api.player_types import PlayerTypeDefinition
from battle_hexes_core.game.sparseboard import SparseBoard
from battle_hexes_core.scenario.scenario import Scenario


class TestFastAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_create_game(self):
        post_response = self.client.post('/games')
        new_game_id = post_response.json().get('id')

        get_response = self.client.get(f'/games/{new_game_id}')
        self.assertEqual(new_game_id, get_response.json().get('id'))

    def test_get_game_invalid_uuid_returns_404(self):
        response = self.client.get('/games/not-a-uuid')
        self.assertEqual(response.status_code, 404)

    def test_get_game_missing_returns_404(self):
        missing_id = uuid4()
        response = self.client.get(f'/games/{missing_id}')
        self.assertEqual(response.status_code, 404)

    @patch('battle_hexes_api.main.scenario_registry')
    def test_list_scenarios(self, mock_registry):
        mock_registry.list_scenarios.return_value = [
            Scenario(id="test-1", name="Test Scenario"),
            Scenario(id="test-2", name="Another Scenario"),
        ]

        response = self.client.get('/scenarios')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {"id": "test-1", "name": "Test Scenario"},
                {"id": "test-2", "name": "Another Scenario"},
            ],
        )
        mock_registry.list_scenarios.assert_called_once_with()

    @patch('battle_hexes_api.main.game_repo')
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

    @patch('battle_hexes_api.main.Combat')
    @patch('battle_hexes_api.main.game_repo')
    def test_resolve_combat_calls_end_game_callback_when_game_over(
        self, mock_game_repo, mock_combat
    ):
        mock_board = MagicMock()
        mock_game = MagicMock()
        mock_game.get_board.return_value = mock_board
        mock_game.is_game_over.return_value = True
        mock_player1 = MagicMock()
        mock_player2 = MagicMock()
        mock_game.get_players.return_value = [mock_player1, mock_player2]
        mock_game_repo.get_game.return_value = mock_game
        mock_combat.return_value.resolve_combat.return_value = MagicMock()

        game_id = "game-123"
        sparse_board_data = {"units": []}

        self.client.post(
            f"/games/{game_id}/combat", json=sparse_board_data
        )

        mock_player1.end_game_cb.assert_called_once_with()
        mock_player2.end_game_cb.assert_called_once_with()

    @patch('battle_hexes_api.main.game_repo')
    def test_generate_movement(self, mock_game_repo):
        mock_plan = MagicMock()
        mock_player = MagicMock()
        mock_player.movement.return_value = [mock_plan]
        mock_plan.to_dict.return_value = {"plan": 1}
        mock_game = MagicMock()
        mock_game.get_current_player.return_value = mock_player
        mock_game.to_game_model.return_value = {"id": "game-456"}
        mock_game_repo.get_game.return_value = mock_game

        game_id = "game-456"
        response = self.client.post(f"/games/{game_id}/movement")

        mock_player.movement.assert_called_once_with()
        mock_game.apply_movement_plans.assert_called_once_with([mock_plan])
        mock_game_repo.update_game.assert_called_once_with(mock_game)
        mock_game.to_game_model.assert_called_once_with()
        mock_plan.to_dict.assert_called_once_with()
        self.assertEqual(
            response.json(),
            {"game": {"id": "game-456"}, "plans": [{"plan": 1}]},
        )

    @patch('battle_hexes_api.main.game_repo')
    def test_end_turn_updates_game_and_returns_game_model(
        self, mock_game_repo
    ):
        mock_game = MagicMock()
        mock_old_player = MagicMock()
        mock_old_player.name = "Alice"
        mock_new_player = MagicMock()
        mock_new_player.name = "Bob"
        mock_game.get_current_player.return_value = mock_old_player
        mock_game.next_player.return_value = mock_new_player
        mock_game.to_game_model.return_value = {
            "id": "game-789",
            "current_player": "Bob"
        }
        mock_game_repo.get_game.return_value = mock_game

        game_id = "game-789"
        sparse_board_data = {"units": []}

        response = self.client.post(
            f"/games/{game_id}/end-turn",
            json=sparse_board_data
        )

        mock_game.update.assert_called_once_with(
            SparseBoard(**sparse_board_data)
        )
        mock_game.get_current_player.assert_called_once_with()
        mock_game.next_player.assert_called_once_with()
        mock_game_repo.update_game.assert_called_once_with(mock_game)
        mock_game.to_game_model.assert_called_once_with()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": "game-789", "current_player": "Bob"}
        )

    @patch('battle_hexes_api.main.game_repo')
    def test_end_turn_calls_end_game_callback_when_game_over(
        self, mock_game_repo
    ):
        mock_player1 = MagicMock()
        mock_player2 = MagicMock()
        mock_game = MagicMock()
        mock_game.get_current_player.return_value = MagicMock()
        mock_game.next_player.return_value = MagicMock()
        mock_game.get_players.return_value = [mock_player1, mock_player2]
        mock_game.is_game_over.return_value = True
        mock_game.to_game_model.return_value = {}
        mock_game_repo.get_game.return_value = mock_game

        game_id = "game-789"
        self.client.post(
            f"/games/{game_id}/end-turn", json={"units": []}
        )

        mock_player1.end_game_cb.assert_called_once_with()
        mock_player2.end_game_cb.assert_called_once_with()

    @patch('battle_hexes_api.main.list_player_types')
    def test_get_player_types(self, mock_list_player_types):
        mock_list_player_types.return_value = (
            PlayerTypeDefinition(id="human", name="Human"),
            PlayerTypeDefinition(id="random", name="Random"),
        )

        response = self.client.get('/player-types')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {"id": "human", "name": "Human"},
                {"id": "random", "name": "Random"},
            ],
        )
        mock_list_player_types.assert_called_once_with()
