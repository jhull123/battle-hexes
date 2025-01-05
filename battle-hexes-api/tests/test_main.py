import unittest
from fastapi.testclient import TestClient
from main import app

class TestFastAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_create_game(self):
        post_response = self.client.post('/games')
        new_game_id = post_response.json().get('id')

        get_response = self.client.get(f'/games/{new_game_id}')
        self.assertEqual(new_game_id, get_response.json().get('id'))

if __name__ == '__main__':
    unittest.main()
