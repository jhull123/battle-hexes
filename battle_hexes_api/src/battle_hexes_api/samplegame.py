from uuid import UUID
import uuid

# from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_agent_rl.multiunitqlearn import MulitUnitQLearnPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class SampleGameCreator:
    """Utility class for constructing game instances."""

    @staticmethod
    def create_sample_game() -> Game:
        """Create a simple two-player game with preset units."""
        board_size = (10, 10)

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

        board = Board(*board_size)

        player1 = RandomPlayer(
            name="Player 1",
            type=PlayerType.CPU,
            factions=[red_faction],
            board=board,
        )

        # repo_root = Path(__file__).resolve().parents[3]
        # q_table_path = repo_root / "battle_agent_rl" / "q_table.json"
        # player2 = QLearningPlayer(
        #    name="Player 2",
        #    type=PlayerType.CPU,
        #    factions=[blue_faction],
        #    board=board,
        #    epsilon=0.0,
        # )
        # player2.load_q_table(q_table_path)

        player2 = MulitUnitQLearnPlayer(
            name="Player 2",
            type=PlayerType.CPU,
            factions=[blue_faction],
            board=board,
        )

        red_unit = Unit(
            UUID("a22c90d0-db87-11d0-8c3a-00c04fd708be", version=4),
            "Red Unit",
            red_faction,
            player1,
            "Infantry",
            2,
            2,
            6,
        )
        red_unit.set_coords(2, 2)

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
        blue_unit.set_coords(8, 9)

        blue_two = Unit(
            uuid.uuid4(),
            "Blue Two",
            blue_faction,
            player2,
            "Scout",
            2,
            2,
            5,
        )
        blue_two.set_coords(9, 5)

        return GameFactory(
            board_size,
            [player1, player2],
            [red_unit, blue_unit, blue_two],
        ).create_game()
