"""Train a multi-unit Q-learning agent on the SampleGame scenario."""

import argparse
import logging
from pathlib import Path
from typing import List

from battle_agent_rl.qlearningplayer import (
    QLearningPlayer,
    QLearningSettingsLoader,
)
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.training.agenttrainer import AgentTrainer
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit
from battle_hexes_core.scenario.scenario_loader import load_scenario_data


DEFAULT_SCENARIO_ID = "elim_1"


logger = logging.getLogger(__name__)


def build_players() -> tuple[RandomPlayer, QLearningPlayer, List[Unit]]:
    """Create players and units matching ``GameCreator``."""

    scenario = load_scenario_data(DEFAULT_SCENARIO_ID)

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
        factions_by_player.setdefault(faction_data.player, []).append(faction)
        if faction_data.player not in player_order:
            player_order.append(faction_data.player)

    if len(player_order) < 2:
        raise ValueError("Scenario must define at least two players")

    random_player = RandomPlayer(
        name=player_order[0],
        type=PlayerType.CPU,
        factions=factions_by_player[player_order[0]],
        board=None,
    )

    rl_settings = QLearningSettingsLoader(logger=logger).load()
    rl_player = QLearningPlayer(
        name=player_order[1],
        type=PlayerType.CPU,
        factions=factions_by_player[player_order[1]],
        board=None,
        **rl_settings,
    )

    players = [random_player, rl_player]
    player_by_faction = {
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

    return random_player, rl_player, units


def main(episodes: int = 5, max_turns: int = 5) -> None:
    """Train the MultiUnit Q-learning player."""

    random_player, rl_player, units = build_players()
    scenario = load_scenario_data(DEFAULT_SCENARIO_ID)

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
