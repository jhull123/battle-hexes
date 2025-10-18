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
        self.assign_factions(scenario, player1, player2)
        return Game(
            players=[player1, player2],
            board=Board(*scenario.board_size)
        )

    def assign_factions(
            self,
            scenario: Scenario,
            player1: Player,
            player2: Player
    ) -> None:
        for faction_data in scenario.factions:
            faction = Faction(
                id=faction_data.id,
                name=faction_data.name,
                color=faction_data.color,
            )
            if faction_data.player == 'Player 1':
                player1.add_faction(faction)
            elif faction_data.player == 'Player 2':
                player2.add_faction(faction)
            else:
                raise NameError("Unknown player: " + faction_data.player)
