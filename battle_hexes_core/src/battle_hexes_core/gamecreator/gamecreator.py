from collections.abc import Sequence

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit
from battle_hexes_core.scenario.scenario import Scenario
from battle_hexes_core.scenario.scenario_loader import load_scenario


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
        _, _, _, game = self.build_game_components(
            scenario,
            (player1, player2),
        )
        return game

    def build_game_components(
        self,
        scenario: Scenario | str,
        players: Sequence[Player],
    ) -> tuple[Scenario, list[Player], list[Unit], Game]:
        """Return the scenario, players, units and a ready ``Game``."""

        if len(players) != 2:
            raise ValueError(
                "GameCreator currently supports exactly two players"
            )

        scenario_obj = (
            load_scenario(scenario)
            if isinstance(scenario, str)
            else scenario
        )

        board = Board(*scenario_obj.board_size)

        players_list = list(players)
        for player in players_list:
            if hasattr(player, "_board"):
                player._board = board

        player1, player2 = players_list
        faction_by_id, player_by_faction_id = self.assign_factions(
            scenario_obj,
            player1,
            player2,
        )
        self.add_units(
            board,
            scenario_obj,
            faction_by_id,
            player_by_faction_id,
        )

        game = Game(
            players=players_list,
            board=board,
        )

        # Persist the original configuration on the ``Game`` instance so the
        # API can expose it when clients fetch the game later.  This allows
        # frontend to recreate new matches using the same scenario and player
        # the types that were originally requested.
        game.scenario_id = scenario_obj.id
        game.player_type_ids = tuple(
            type(player).__name__ for player in players_list
        )

        units = board.get_units()

        return scenario_obj, players_list, units, game

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
        scenario: Scenario,
        faction_by_id: dict[str, Faction],
        player_by_faction_id: dict[str, Player],
    ) -> None:
        if not scenario.units:
            return

        unit_by_id = {unit.id: unit for unit in scenario.units}
        for hex_entry in scenario.hex_data:
            if not hex_entry.units:
                continue

            row, column = hex_entry.coords
            for unit_id in hex_entry.units:
                unit_data = unit_by_id.get(unit_id)
                if unit_data is None:
                    raise NameError(f"Unknown unit: {unit_id}")

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

                board.add_unit(unit, row, column)
