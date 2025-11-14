from pathlib import Path
from typing import Sequence

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.gamecreator.gamecreator import (
    GameCreator as CoreGameCreator,
)
from battle_hexes_core.scenario.scenario_loader import load_scenario
from battle_hexes_core.unit.faction import Faction
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
        scenario = load_scenario(scenario_id)

        player_order: list[str] = []
        for faction in scenario.factions:
            if faction.player not in player_order:
                player_order.append(faction.player)

        if len(player_order) != len(player_type_ids):
            raise ValueError(
                "Number of player types does not match scenario configuration"
            )

        players = []
        for index, player_name in enumerate(player_order):
            type_id = player_type_ids[index]
            player = GameCreator._create_player(
                type_id,
                name=player_name,
                factions=[],
                board=None,
            )
            players.append(player)

        creator = CoreGameCreator()
        _, players, _, game = creator.build_game_components(
            scenario,
            players,
        )

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
