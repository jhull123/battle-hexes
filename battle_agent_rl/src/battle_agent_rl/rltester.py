"""Evaluate a trained Q-learning agent against the SampleGame scenario."""

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


logger = logging.getLogger(__name__)


def _build_q_learning_factory(
    settings: dict,
) -> Callable[[str, str, list[Faction], Board], QLearningPlayer]:
    """Return a factory for evaluation-mode Q-learning players."""

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
    """Evaluate the Q-learning player against a random opponent."""

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
            "No existing Q-table found at %s, using default weights",
            q_table_path,
        )

    rl_player.disable_exploration()
    rl_player.disable_learning()

    agent_trainer = AgentTrainer(game_factory, episodes, max_turns=max_turns)
    game_results = agent_trainer.train()
    wins = game_results.count_wins()
    losses = game_results.count_losses()
    draws = game_results.count_draws()
    exchanges = game_results.count_exchanges()
    total = wins + losses + draws + exchanges
    pct = (lambda c: (c / total * 100) if total else 0.0)
    wins_pct = pct(wins)
    losses_pct = pct(losses)
    draws_pct = pct(draws)
    exchanges_pct = pct(exchanges)
    pct_strs = {
        "Wins": f"{wins_pct:.1f}%",
        "Losses": f"{losses_pct:.1f}%",
        "Draws": f"{draws_pct:.1f}%",
        "Exchanges": f"{exchanges_pct:.1f}%",
    }
    pct_width = max(len(s) for s in pct_strs.values()) if pct_strs else 0
    print(f"{'Wins':<9}: {wins:>3} ({pct_strs['Wins']:>{pct_width}})")
    print(f"{'Losses':<9}: {losses:>3} ({pct_strs['Losses']:>{pct_width}})")
    print(f"{'Draws':<9}: {draws:>3} ({pct_strs['Draws']:>{pct_width}})")
    print(
        f"{'Exchanges':<9}: {exchanges:>3} "
        f"({pct_strs['Exchanges']:>{pct_width}})"
    )

    score = 2 * wins_pct - 2 * losses_pct - 1 * draws_pct
    print(f"{'Score':<9}: {score:>6.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Test the multi-unit Q-learning player "
            "against a random opponent in the SampleGame scenario"
        ),
    )
    parser.add_argument(
        "episodes",
        nargs="?",
        type=int,
        default=5,
        help="number of test episodes to run",
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
    logger.info("Testing with args %s", args)
    main(args.episodes, args.max_turns)
