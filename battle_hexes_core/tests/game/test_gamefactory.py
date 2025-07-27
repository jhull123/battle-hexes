import unittest
import uuid
from unittest.mock import patch

from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestGameFactory(unittest.TestCase):
    def setUp(self):
        self.board_size = (3, 3)
        self.faction = Faction(id=uuid.uuid4(), name="F", color="red")
        self.player = Player(
            name="P",
            type=PlayerType.CPU,
            factions=[self.faction],
        )
        self.unit1 = Unit(
            uuid.uuid4(),
            "U1",
            self.faction,
            self.player,
            "I",
            1,
            1,
            1,
            row=0,
            column=0,
        )
        self.unit2 = Unit(
            uuid.uuid4(),
            "U2",
            self.faction,
            self.player,
            "I",
            1,
            1,
            1,
            row=1,
            column=1,
        )

    def test_create_game_uses_initial_positions(self):
        factory = GameFactory(
            self.board_size,
            [self.player],
            [self.unit1, self.unit2],
        )
        game = factory.create_game()
        coords = [u.get_coords() for u in game.get_board().get_units()]
        self.assertIn((0, 0), coords)
        self.assertIn((1, 1), coords)

    def test_create_game_randomizes_positions(self):
        with patch(
            "battle_hexes_core.game.gamefactory.choice",
            side_effect=[(0, 2), (1, 0)],
        ):
            factory = GameFactory(
                self.board_size,
                [self.player],
                [self.unit1, self.unit2],
                randomize_positions=True,
            )
            game = factory.create_game()
        coords = [u.get_coords() for u in game.get_board().get_units()]
        self.assertCountEqual(coords, [(0, 2), (1, 0)])
