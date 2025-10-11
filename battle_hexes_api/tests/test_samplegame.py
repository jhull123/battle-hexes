import unittest

from battle_hexes_api.samplegame import SampleGameCreator


class TestSampleGameCreator(unittest.TestCase):
    def test_create_sample_game_uses_scenario_data(self):
        game = SampleGameCreator.create_sample_game(
            "elim_1", ["human", "random"]
        )

        board = game.get_board()
        self.assertEqual(board.get_rows(), 10)
        self.assertEqual(board.get_columns(), 10)

        unit_positions = {
            unit.get_id(): unit.get_coords()
            for unit in board.get_units()
        }
        self.assertEqual(
            unit_positions,
            {
                "red_unit_1": (2, 2),
                "blue_unit_1": (8, 9),
                "blue_unit_2": (9, 5),
            },
        )

        players = game.get_players()
        self.assertEqual(
            [player.name for player in players],
            ["Player 1", "Player 2"],
        )
        self.assertEqual(
            [
                [faction.id for faction in player.factions]
                for player in players
            ],
            [["red faction"], ["blue faction"]],
        )

    def test_create_sample_game_requires_matching_player_count(self):
        with self.assertRaises(ValueError):
            SampleGameCreator.create_sample_game("elim_1", ["human"])


if __name__ == "__main__":  # pragma: no cover - convenience
    unittest.main()
