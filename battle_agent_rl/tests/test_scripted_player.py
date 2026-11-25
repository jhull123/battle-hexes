from copy import deepcopy
import random

from battle_agent_rl.scripted import ScriptedPlayer
from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


def test_scripted_player_does_not_order_move_even_when_one_is_legal():
    faction = Faction("red", "Red", "#C81010")
    player = ScriptedPlayer("Scripted", factions=[faction])
    board = Board(2, 2)
    unit = Unit("red-1", "Red Unit", faction, player, "Infantry", 2, 2, 2)
    board.add_unit(unit, 0, 0)
    start = board.get_hex(0, 0)
    assert player.type is PlayerType.CPU
    assert player.owns(unit)
    assert board.get_hex(0, 1) in board.get_reachable_hexes(
        unit, start, unit.current_turn_movement_points_remaining
    )
    player_state = deepcopy(vars(player))
    rng_state = random.getstate()

    for _ in range(2):
        assert player.movement() == []
        player.movement_cb()
        player.combat_results(CombatResults())
        player.end_game_cb()

    assert vars(player) == player_state
    assert board.get_units() == [unit]
    assert unit.get_coords() == (0, 0)
    assert unit.current_turn_movement_points_remaining == 2
    assert random.getstate() == rng_state
