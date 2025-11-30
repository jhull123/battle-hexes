"""Train a multi-unit Q-learning agent on the SampleGame scenario."""

import argparse
import logging
from pathlib import Path

from battle_agent_rl.qlearningplayer import (
    QLearningPlayer,
    QLearningSettingsLoader,
)
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario import Scenario
from battle_hexes_core.training.agenttrainer import AgentTrainer
from battle_hexes_core.unit.unit import Unit


DEFAULT_SCENARIO_ID = "elim_1"


logger = logging.getLogger(__name__)


def build_players() -> tuple[
    Scenario,
    RandomPlayer,
    QLearningPlayer,
    list[Unit],
]:
    """Create players and units matching ``GameCreator`` configuration."""

    rl_settings = QLearningSettingsLoader(logger=logger).load()

    players = [
        RandomPlayer(
            name="Player 1",
            type=PlayerType.CPU,
            factions=[],
            board=None,
        ),
        QLearningPlayer(
            name="Player 2",
            type=PlayerType.CPU,
            factions=[],
            board=None,
            **rl_settings,
        ),
    ]

    creator = GameCreator()
    scenario, players, units, _ = creator.build_game_components(
        DEFAULT_SCENARIO_ID,
        players,
    )

    random_player, rl_player = players
    return scenario, random_player, rl_player, units


def main(episodes: int = 5, max_turns: int = 5) -> None:
    """Train the MultiUnit Q-learning player."""

    scenario, random_player, rl_player, units = build_players()

    q_table_path = Path("q_table.pkl")
    if q_table_path.exists():
        rl_player.load_q_table(str(q_table_path))
        logger.info("Loaded existing Q-table from %s", q_table_path)
    else:
        logger.info(
            "No existing Q-table found at %s, starting fresh", q_table_path
        )

    game_factory = GameFactory(
        board_size=scenario.board_size,
        players=[random_player, rl_player],
        units=units,
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
