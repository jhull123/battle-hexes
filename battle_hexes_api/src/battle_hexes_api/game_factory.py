from uuid import UUID

from battle_agent_random.randomplayer import RandomPlayer
from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class GameFactory:
    """Utility class for constructing game instances."""

    @staticmethod
    def create_sample_game() -> Game:
        # TODO refactor to use the create_game method when ready
        """Create a simple two-player game with preset units."""
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

        board = Board(10, 25)

        player1 = RandomPlayer(
            name="Player 1",
            type=PlayerType.CPU,
            factions=[red_faction],
            board=board
        )
        player1 = Player(
            name="Player 1",
            type=PlayerType.HUMAN,
            factions=[red_faction],
            board=board
        )

        player2 = QLearningPlayer(
            name="Player 2",
            type=PlayerType.CPU,
            factions=[blue_faction],
            board=board
        )

        game = Game([player1, player2], board)

        red_unit = Unit(
            UUID("a22c90d0-db87-11d0-8c3a-00c04fd708be", version=4),
            "Red Unit",
            red_faction,
            player1,
            "Infantry",
            2,
            2,
            1,
        )
        game.board.add_unit(red_unit, 1, 1)

        blue_unit = Unit(
            UUID("c9a440d2-2b0a-4730-b4c6-da394b642c61", version=4),
            "Blue Unit",
            blue_faction,
            player2,
            "Infantry",
            4,
            4,
            4,
        )
        game.board.add_unit(blue_unit, 9, 20)

        return game

    def create_game(
            self,
            board_size: tuple[int, int],
            players: list[Player],
            units: list[Unit]
            ) -> Game:
        # TODO implement me!
        return None
