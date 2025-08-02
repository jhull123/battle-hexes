"""Utility to train a simple Q-learning agent against a random opponent."""

import argparse
import uuid
from typing import List

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.training.agenttrainer import AgentTrainer
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


def build_players() -> tuple[RandomPlayer, QLearningPlayer, List[Unit]]:
    """Create players and their starting units."""
    random_player_factions = [
        Faction(id=uuid.uuid4(), name="Random Faction", color="red")
    ]

    random_player = RandomPlayer(
        name="Random Player",
        type=PlayerType.CPU,
        factions=random_player_factions,
        board=None,  # Board will be set later
    )

    random_unit = Unit(
        id=uuid.uuid4(),
        name="Random Unit",
        faction=random_player_factions[0],
        player=random_player,
        type="Infantry",
        attack=2,
        defense=2,
        move=6,
        row=0,
        column=0,
    )

    rl_player_factions = [
        Faction(id=uuid.uuid4(), name="RL Faction", color="blue")
    ]

    rl_player = QLearningPlayer(
        name="Q Learning Player",
        type=PlayerType.CPU,
        factions=rl_player_factions,
        board=None,  # Board will be set later
    )

    rl_unit_1 = Unit(
        id=uuid.uuid4(),
        name="RL Unit 1",
        faction=rl_player_factions[0],
        player=rl_player,
        type="Infantry",
        attack=4,
        defense=4,
        move=4,
        row=9,
        column=9,
    )

    # rl_unit_2 = Unit(
    #    id=uuid.uuid4(),
    #     name="RL Unit 2",
    #     faction=rl_player_factions[0],
    #     player=rl_player,
    #     type="Heavy Infantry",
    #     attack=100,
    #     defense=40,
    #     move=5,
    #     row=0,
    #     column=9,
    # )

    return random_player, rl_player, [random_unit, rl_unit_1]


def main(episodes: int = 5) -> None:
    """Train the Q-learning player for a given number of episodes."""
    random_player, rl_player, units = build_players()

    game_factory = GameFactory(
        board_size=(10, 10),
        players=[random_player, rl_player],
        units=units,
        randomize_positions=True
    )

    agent_trainer = AgentTrainer(game_factory, episodes)
    agent_trainer.train()
    rl_player.print_q_table()
    rl_player.save_q_table("q_table.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train the Q-learning player against a random opponent"
    )
    parser.add_argument(
        "episodes",
        nargs="?",
        type=int,
        default=5,
        help="number of training episodes to run",
    )
    args = parser.parse_args()
    main(args.episodes)
