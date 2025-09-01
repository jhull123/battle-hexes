"""Train a multi-unit Q-learning agent against a random opponent."""

import argparse
import random
import uuid
import logging
from typing import List

from battle_agent_rl.multiunitqlearn import MulitUnitQLearnPlayer
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.training.agenttrainer import AgentTrainer
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


# module logger
logger = logging.getLogger(__name__)


# (attack, defense, movement) with weights for selection
_UNIT_STATS = [
    ((1, 1, 6), 10),
    ((2, 2, 4), 10),
    ((2, 2, 6), 30),  # second most common
    ((4, 4, 4), 50),  # most common
    ((5, 4, 4), 2),   # rare
]


def _random_stats() -> tuple[int, int, int]:
    """Return a random (attack, defense, move) tuple."""
    stats, weights = zip(*_UNIT_STATS)
    attack, defense, move = random.choices(stats, weights=weights, k=1)[0]
    return attack, defense, move


def _generate_units(
    player: RandomPlayer | MulitUnitQLearnPlayer, count: int, name_prefix: str
) -> List[Unit]:
    """Create ``count`` units for ``player`` with random stats."""
    units: List[Unit] = []
    for i in range(count):
        attack, defense, move = _random_stats()
        unit = Unit(
            id=uuid.uuid4(),
            name=f"{name_prefix} Unit {i + 1}",
            faction=player.factions[0],
            player=player,
            type="Infantry",
            attack=attack,
            defense=defense,
            move=move,
            row=0,
            column=0,
        )
        units.append(unit)
    return units


def build_players() -> tuple[RandomPlayer, MulitUnitQLearnPlayer, List[Unit]]:
    """Create players and a random distribution of starting units."""
    random_player_factions = [
        Faction(id=uuid.uuid4(), name="Random Faction", color="red")
    ]
    rl_player_factions = [
        Faction(id=uuid.uuid4(), name="RL Faction", color="blue")
    ]

    random_player = RandomPlayer(
        name="Random Player",
        type=PlayerType.CPU,
        factions=random_player_factions,
        board=None,  # Board will be set later
    )

    rl_player = MulitUnitQLearnPlayer(
        name="MultiUnit Q Player",
        type=PlayerType.CPU,
        factions=rl_player_factions,
        board=None,  # Board will be set later
    )

    total_units = random.randint(2, 10)
    random_count = random.randint(1, total_units - 1)
    rl_count = total_units - random_count

    random_units = _generate_units(random_player, random_count, "Random")
    rl_units = _generate_units(rl_player, rl_count, "RL")

    return random_player, rl_player, random_units + rl_units


def main(episodes: int = 5, max_turns: int = 5) -> None:
    """Train the MultiUnit Q-learning player."""
    random_player, rl_player, units = build_players()

    game_factory = GameFactory(
        board_size=(16, 16),
        players=[random_player, rl_player],
        units=units,
        randomize_positions=True,
    )

    agent_trainer = AgentTrainer(game_factory, episodes, max_turns=max_turns)
    agent_trainer.train()
    # rl_player.print_q_table()
    rl_player.save_q_table("q_multiunit_table.pkl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Train the multi-unit Q-learning player "
            "against a random opponent"
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
        default=5,
        help="maximum number of turns per game",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Training with args %s", args)
    main(args.episodes, args.max_turns)
