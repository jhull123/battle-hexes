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
            id="human_red_faction",
            name="Red Faction",
            color="#C81010",
        )

        blue_faction = Faction(
            id="human_blue_faction",
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
            "human_red_unit_1",
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
            "human_red_unit_2",
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
            "human_blue_unit_1",
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
            "human_blue_unit_2",
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
