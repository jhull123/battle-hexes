from pathlib import Path
from typing import Sequence

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.scenario.scenario_loader import load_scenario_data
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit
from pydantic import PrivateAttr


class SampleHumanPlayer(Player):
    """Minimal representation of a human-controlled player."""

    _board: Board = PrivateAttr(default=None)

    def __init__(
        self,
        name: str,
        factions: list[Faction],
        board: Board,
    ) -> None:
        super().__init__(name=name, type=PlayerType.HUMAN, factions=factions)
        self._board = board

    def movement(self):  # pragma: no cover
        """Human players plan movement client-side."""
        return []

    def combat_results(self, combat_results):  # pragma: no cover
        """Human players review combat results client-side."""
        return None


class GameCreator:
    """Utility class for constructing game instances."""

    @staticmethod
    def create_sample_game(
        scenario_id: str, player_type_ids: Sequence[str]
    ) -> Game:
        """Create a simple two-player game with preset units.

        Parameters
        ----------
        scenario_id:
            Currently unused placeholder that allows callers to select between
            future sample scenarios.
        player_type_ids:
            Sequence of player identifiers (``human``, ``random``,
            ``q-learning``) used to configure the players participating in the
            game.
        """
        scenario = load_scenario_data(scenario_id)
        board_size = scenario.board_size
        board = Board(*board_size)

        factions_by_player: dict[str, list[Faction]] = {}
        factions_by_id: dict[str, Faction] = {}
        player_order: list[str] = []

        for faction_data in scenario.factions:
            faction = Faction(
                id=faction_data.id,
                name=faction_data.name,
                color=faction_data.color,
            )
            factions_by_id[faction.id] = faction
            factions_by_player.setdefault(
                faction_data.player, []
            ).append(faction)
            if faction_data.player not in player_order:
                player_order.append(faction_data.player)

        if len(player_order) != len(player_type_ids):
            raise ValueError(
                "Number of player types does not match scenario configuration"
            )

        players = []
        for index, player_name in enumerate(player_order):
            type_id = player_type_ids[index]
            factions = factions_by_player[player_name]
            player = GameCreator._create_player(
                type_id,
                name=player_name,
                factions=factions,
                board=board,
            )
            players.append(player)

        player_by_faction: dict[str, Player] = {
            faction.id: player
            for player in players
            for faction in player.factions
        }

        units: list[Unit] = []
        for unit_data in scenario.units:
            faction = factions_by_id[unit_data.faction]
            owner = player_by_faction[faction.id]
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
            start_row, start_col = unit_data.starting_coords
            unit.set_coords(start_row, start_col)
            units.append(unit)

        game = GameFactory(
            board_size,
            players,
            units,
        ).create_game()

        # Persist the original configuration on the ``Game`` instance so the
        # API can expose it when clients fetch the game later.  This allows the
        # frontend to recreate new matches using the same scenario and player
        # types that were originally requested.
        game.scenario_id = scenario_id
        game.player_type_ids = list(player_type_ids)

        return game

    @staticmethod
    def _create_player(
        type_id: str,
        name: str,
        factions: list[Faction],
        board: Board,
    ) -> Player:
        """Instantiate a player for ``type_id``."""

        if type_id == "human":
            return SampleHumanPlayer(
                name=name,
                factions=factions,
                board=board,
            )

        if type_id == "random":
            return RandomPlayer(
                name=name,
                type=PlayerType.CPU,
                factions=factions,
                board=board,
            )

        if type_id == "q-learning":
            repo_root = Path(__file__).resolve().parents[3]
            player = QLearningPlayer(
                name=name,
                type=PlayerType.CPU,
                factions=factions,
                board=board,
                epsilon=0.0,
            )
            q_table_path = repo_root / "battle_agent_rl" / "q_table.pkl"
            player.load_q_table(q_table_path)
            return player

        raise ValueError(f"Unsupported player type '{type_id}'")
