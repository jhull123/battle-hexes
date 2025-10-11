"""Train a multi-unit Q-learning agent on the SampleGame scenario."""

import argparse
import logging
from collections.abc import Callable
from pathlib import Path

from battle_agent_rl.qlearningplayer import (
    QLearningPlayer,
    QLearningSettingsLoader,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.training.agenttrainer import AgentTrainer
from battle_hexes_core.unit.faction import Faction


DEFAULT_SCENARIO_ID = "elim_1"
PLAYER_TYPE_IDS = ("random", "q-learning")


# module logger
logger = logging.getLogger(__name__)


def _build_q_learning_factory(
    settings: dict,
) -> Callable[[str, str, list[Faction], Board], QLearningPlayer]:
    """Return a factory that creates configured ``QLearningPlayer`` instances."""

    def _factory(
        _type_id: str,
        name: str,
        factions: list[Faction],
        board: Board,
    ) -> QLearningPlayer:
        return QLearningPlayer(
            name=name,
            type=PlayerType.CPU,
            factions=factions,
            board=board,
            **settings,
        )

    return _factory


def main(episodes: int = 5, max_turns: int = 5) -> None:
    """Train the MultiUnit Q-learning player."""

    from battle_hexes_api.gamecreator import GameCreator

    settings = QLearningSettingsLoader(logger=logger).load()
    game_factory = GameCreator.create_sample_game_factory(
        DEFAULT_SCENARIO_ID,
        PLAYER_TYPE_IDS,
        player_factories={"q-learning": _build_q_learning_factory(settings)},
    )

    rl_player = next(
        player
        for player in game_factory.players
        if isinstance(player, QLearningPlayer)
    )

    q_table_path = Path("q_table.pkl")
    if q_table_path.exists():
        rl_player.load_q_table(str(q_table_path))
        logger.info("Loaded existing Q-table from %s", q_table_path)
    else:
        logger.info(
            "No existing Q-table found at %s, starting fresh", q_table_path
        )

    agent_trainer = AgentTrainer(game_factory, episodes, max_turns=max_turns)
    agent_trainer.train()
    rl_player.save_q_table(str(q_table_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Train the multi-unit Q-learning player "
            "against a random opponent in the SampleGame scenario"
        ),
    )
    parser.add_argument(
        "episodes",
        nargs="?",
        type=int,
        default=5,
        help="number of training episodes to run",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="maximum number of turns per game",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Training with args %s", args)
    main(args.episodes, args.max_turns)
