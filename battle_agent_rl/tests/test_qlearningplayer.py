import uuid

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit
from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.combat.combatresults import CombatResults


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


def test_calculate_reward():
    board = Board(1, 1)
    faction = Faction(id=uuid.uuid4(), name="F", color="red")
    agent = QLearningPlayer(
        name="QL",
        type=PlayerType.CPU,
        factions=[faction],
        board=board,
    )

    # Attacker case
    agent._last_actions = {"x": ("s", "a")}
    results = CombatResults()
    results.add_battle(
        CombatResultData((1, 1), 1, CombatResult.DEFENDER_ELIMINATED)
    )
    assert agent.calculate_reward(results) == 1

    results = CombatResults()
    results.add_battle(
        CombatResultData((1, 1), 1, CombatResult.ATTACKER_ELIMINATED)
    )
    assert agent.calculate_reward(results) == -1

    # Defender case
    agent._last_actions = {}
    results = CombatResults()
    results.add_battle(
        CombatResultData((1, 1), 1, CombatResult.ATTACKER_ELIMINATED)
    )
    assert agent.calculate_reward(results) == 1
    results = CombatResults()
    results.add_battle(
        CombatResultData((1, 1), 1, CombatResult.DEFENDER_ELIMINATED)
    )
    assert agent.calculate_reward(results) == -1


def test_combat_results_updates_q_table():
    board = Board(2, 2)
    faction_a = Faction(id=uuid.uuid4(), name="A", color="blue")
    faction_b = Faction(id=uuid.uuid4(), name="B", color="green")
    other_player = Player(name="O", type=PlayerType.CPU, factions=[faction_b])
    agent = QLearningPlayer(
        name="QL",
        type=PlayerType.CPU,
        factions=[faction_a],
        board=board,
        alpha=1.0,
        gamma=0.0,
        epsilon=0.0,
    )
    ally = Unit(uuid.uuid4(), "Ally", faction_a, agent, "Inf", 1, 1, 1)
    enemy = Unit(
        uuid.uuid4(),
        "Enemy",
        faction_b,
        other_player,
        "Inf",
        1,
        1,
        1,
    )
    board.add_unit(ally, 0, 0)
    board.add_unit(enemy, 0, 1)

    state = agent.board_state()
    action = (ally.get_id(), ally.row, ally.column)
    agent._last_actions = {str(ally.get_id()): (state, action)}

    results = CombatResults()
    results.add_battle(
        CombatResultData((1, 1), 1, CombatResult.DEFENDER_ELIMINATED)
    )
    board.remove_units(enemy)

    agent.combat_results(results)

    assert agent.q_table[(state, action)] == 1
