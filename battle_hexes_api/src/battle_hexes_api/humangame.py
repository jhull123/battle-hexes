from uuid import UUID

from battle_hexes_core.game.game import Game
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class HumanGameCreator:
    """Utility class for constructing a human-vs-human game."""

    @staticmethod
    def create_human_game() -> Game:
        """Create a two-player human game with two units each."""
        board_size = (10, 25)

        red_faction = Faction(
            id=UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479", version=4),
            name="Red Faction",
            color="#C81010",
        )

        blue_faction = Faction(
            id=UUID("38400000-8cf0-11bd-b23e-10b96e4ef00d", version=4),
            name="Blue Faction",
            color="#4682B4",
        )

        player1 = Player(
            name="Player 1",
            type=PlayerType.HUMAN,
            factions=[red_faction],
        )

        player2 = Player(
            name="Player 2",
            type=PlayerType.HUMAN,
            factions=[blue_faction],
        )

        red_unit1 = Unit(
            UUID("a22c90d0-db87-11d0-8c3a-00c04fd708be", version=4),
            "Red Unit 1",
            red_faction,
            player1,
            "Infantry",
            2,
            2,
            6,
        )
        red_unit1.set_coords(2, 2)

        red_unit2 = Unit(
            UUID("a22c90d0-db87-11d0-8c3a-00c04fd708bf", version=4),
            "Red Unit 2",
            red_faction,
            player1,
            "Infantry",
            2,
            2,
            6,
        )
        red_unit2.set_coords(3, 2)

        blue_unit1 = Unit(
            UUID("c9a440d2-2b0a-4730-b4c6-da394b642c61", version=4),
            "Blue Unit 1",
            blue_faction,
            player2,
            "Infantry",
            4,
            4,
            4,
        )
        blue_unit1.set_coords(8, 19)

        blue_unit2 = Unit(
            UUID("c9a440d2-2b0a-4730-b4c6-da394b642c62", version=4),
            "Blue Unit 2",
            blue_faction,
            player2,
            "Infantry",
            4,
            4,
            4,
        )
        blue_unit2.set_coords(7, 19)

        return GameFactory(
            board_size,
            [player1, player2],
            [red_unit1, red_unit2, blue_unit1, blue_unit2],
        ).create_game()
