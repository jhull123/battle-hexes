import uuid

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


def test_qlearning_update_rule():
    board = Board(1, 1)
    faction = Faction(id=uuid.uuid4(), name="F", color="red")
    player = QLearningPlayer(
        name="QL",
        type=PlayerType.CPU,
        factions=[faction],
        board=board,
        alpha=0.5,
        gamma=0.5,
        epsilon=0.0,
    )
    state = "s1"
    next_state = "s2"
    player.update_q(state, "a", reward=1.0, next_state=next_state)
    expected = 0.5 * (1.0 + 0.5 * 0 - 0)
    assert player.q_table[(state, "a")] == expected


def test_elimination_reward():
    board = Board(2, 2)
    faction_a = Faction(id=uuid.uuid4(), name="A", color="blue")
    faction_b = Faction(id=uuid.uuid4(), name="B", color="green")
    player = Player(name="P", type=PlayerType.CPU, factions=[faction_a])
    agent = QLearningPlayer(
        name="QL",
        type=PlayerType.CPU,
        factions=[faction_a],
        board=board,
    )
    ally = Unit(uuid.uuid4(), "Ally", faction_a, player, "Inf", 1, 1, 1)
    enemy = Unit(uuid.uuid4(), "Enemy", faction_b, player, "Inf", 1, 1, 1)
    # Before state has both units
    before = [ally, enemy]
    # After state loses the enemy
    after = [ally]
    assert agent.elimination_reward(before, after) == 1
    # After losing the ally
    after = [enemy]
    assert agent.elimination_reward(before, after) == -1
