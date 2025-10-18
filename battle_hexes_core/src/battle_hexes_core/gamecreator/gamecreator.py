from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit
from battle_hexes_core.scenario.scenario import Scenario, ScenarioUnit


class GameCreator:
    """
    A class for creating and managing game instances.
    This class will be responsible for handling game creation and
    initialization.
    """

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
        faction_by_id, player_by_faction_id = self.assign_factions(
            scenario,
            player1,
            player2,
        )
        self.add_units(
            board,
            scenario.units,
            faction_by_id,
            player_by_faction_id,
        )
        return Game(
            players=[player1, player2],
            board=board
        )

    def assign_factions(
            self,
            scenario: Scenario,
            player1: Player,
            player2: Player
    ) -> tuple[dict[str, Faction], dict[str, Player]]:
        faction_by_id: dict[str, Faction] = {}
        player_by_faction_id: dict[str, Player] = {}
        if not scenario.factions:
            return faction_by_id, player_by_faction_id

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

            faction_by_id[faction.id] = faction
            player_by_faction_id[faction.id] = player
            player.add_faction(faction)

        return faction_by_id, player_by_faction_id

    def add_units(
        self,
        board: Board,
        units: tuple[ScenarioUnit, ...],
        faction_by_id: dict[str, Faction],
        player_by_faction_id: dict[str, Player],
    ) -> None:
        for unit_data in units:
            try:
                faction = faction_by_id[unit_data.faction]
                owner = player_by_faction_id[unit_data.faction]
            except KeyError as exc:
                message = f"Unknown faction: {unit_data.faction}"
                raise NameError(message) from exc

            unit = Unit(
                unit_data.id,
                unit_data.name,
                faction,
                owner,
                unit_data.type,
                unit_data.attack,
                unit_data.defense,
                unit_data.movement,
            )

            row, column = unit_data.starting_coords
            board.add_unit(unit, row, column)
