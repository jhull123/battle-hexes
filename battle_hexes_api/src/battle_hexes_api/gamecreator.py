from collections.abc import Mapping, Sequence
from pathlib import Path

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_agent_rl.scripted import (
    ScriptedGameOpening,
    ScriptedOpening,
    ScriptedPlayer,
)
from battle_agent_rl.scripted.opening import OpeningSampler
from battle_hexes_api.scripted_assignment_logging import (
    attach_reinforcement_logging,
    log_scripted_openings,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.gamecreator.gamecreator import (
    GameCreator as CoreGameCreator,
)
from battle_hexes_core.scenario.scenario import Scenario
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


class ExperimentalPpoPlayer(Player):
    """The API's atomic order command, never batch movement, owns this side."""

    def movement(self):
        raise RuntimeError("Use the live PPO order command")

    def combat_results(self, combat_results):
        pass


class GameCreator:
    """Utility class for constructing game instances."""

    @staticmethod
    def create_sample_game(
        scenario_id: str,
        player_type_ids: Sequence[str],
        *,
        scripted_openings: Mapping[int, ScriptedOpening] | None = None,
        seed: int | None = None,
    ) -> Game:
        """Create a game with per-seat options and one opening seed."""
        from battle_hexes_api.agent_integrations import integrations
        from battle_hexes_api.persistence.errors import (
            SavedGameIncompatibleError,
        )

        try:
            integration = integrations.select(scenario_id, player_type_ids,
                                              False)
        except SavedGameIncompatibleError as error:
            raise ValueError(
                "Experimental PPO requires the first seat, its fixed 9x9 "
                "scenario and a supported opponent") from error

        scenario = load_scenario(scenario_id)
        openings = GameCreator._resolve_scripted_openings(
            player_type_ids, scripted_openings,
        )
        game_opening = ScriptedGameOpening(seed)
        players = GameCreator._create_players(
            scenario, player_type_ids, openings, game_opening,
        )
        _, _, _, game = CoreGameCreator().build_game_components(
            scenario, players,
        )
        game.scenario_id = scenario_id
        game.player_type_ids = list(player_type_ids)
        log_scripted_openings(game, openings)
        attach_reinforcement_logging(game)
        integration.initial_state(game)
        return game

    @staticmethod
    def _resolve_scripted_openings(
        player_type_ids: Sequence[str],
        configured: Mapping[int, ScriptedOpening] | None,
    ) -> dict[int, ScriptedOpening]:
        default = ScriptedOpening()
        openings = {
            seat: default for seat, type_id in enumerate(player_type_ids)
            if type_id == "scripted"
        }
        for seat, opening in (configured or {}).items():
            if type(seat) is not int or seat not in openings:
                raise ValueError("Opening options require a scripted seat")
            openings[seat] = opening
        return openings

    @staticmethod
    def _create_players(
        scenario: Scenario, player_type_ids: Sequence[str],
        openings: Mapping[int, ScriptedOpening],
        game_opening: ScriptedGameOpening,
    ) -> list[Player]:
        player_order: list[str] = []
        for faction in scenario.factions:
            if faction.player not in player_order:
                player_order.append(faction.player)

        if len(player_order) != len(player_type_ids):
            raise ValueError(
                "Number of player types does not match scenario configuration"
            )

        return [
            GameCreator._create_player(
                type_id,
                name=player_name,
                factions=[],
                board=None,
                opening_sampler=game_opening.for_seat(index, openings[index])
                if index in openings else None,
            )
            for index, (player_name, type_id) in enumerate(
                zip(player_order, player_type_ids, strict=True)
            )
        ]

    @staticmethod
    def _create_player(
        type_id: str,
        name: str,
        factions: list[Faction],
        board: Board | None,
        *,
        opening_sampler: OpeningSampler | None = None,
    ) -> Player:
        """Instantiate a player for ``type_id``."""

        if type_id == "human":
            return SampleHumanPlayer(
                name=name,
                factions=factions,
                board=board,
            )

        if type_id == "ppo-9x9-experimental":
            return ExperimentalPpoPlayer(name=name, type=PlayerType.CPU,
                                         factions=factions)

        if type_id == "scripted":
            return ScriptedPlayer(
                name=name, factions=factions, board=board,
                opening_sampler=opening_sampler,
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
