from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.scenario.scenario import Scenario


class GameCreator:
    """
    A class for creating and managing game instances.
    This class will be responsible for handling game creation and
    initialization.
    """

    def __init__(self):
        """Initialize a new GameCreator instance."""
        pass

    def create_game(
        self,
        scenario: Scenario,
        player1: Player,
        player2: Player
    ) -> Game:
        """
        Creates a new game instance with the given scenario and players.

        Args:
            scenario: The game scenario to use
            player1: The first player
            player2: The second player

        Returns:
            Game: A new game instance with the specified configuration.
        """
        board = Board(*scenario.board_size)
        self.assign_factions(scenario, player1, player2)
        self.add_units(board, scenario.units)
        return Game(
            players=[player1, player2],
            board=board
        )

    def assign_factions(
            self,
            scenario: Scenario,
            player1: Player,
            player2: Player
    ) -> None:
        if not scenario.factions:
            return

        player_map = {
            "Player 1": player1,
            "Player 2": player2,
            getattr(player1, "name", None): player1,
            getattr(player2, "name", None): player2,
        }

        for faction_data in scenario.factions:
            faction = Faction(
                id=faction_data.id,
                name=faction_data.name,
                color=faction_data.color,
            )
            try:
                player = player_map[faction_data.player]
            except KeyError as exc:
                message = f"Unknown player: {faction_data.player}"
                raise NameError(message) from exc

            player.add_faction(faction)

    def add_units(self, board: Board, units):
        # TODO implement me and add a type hint to the units parameter
        pass
