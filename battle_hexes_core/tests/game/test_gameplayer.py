import unittest
import uuid
from unittest.mock import patch, MagicMock
from pydantic import PrivateAttr

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.gameplayer import GamePlayer
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class DummyCPUPlayer(Player):
    _ended: bool = PrivateAttr(False)

    def __init__(self, name, factions):
        super().__init__(name=name, type=PlayerType.CPU, factions=factions)

    def movement(self):
        return []

    def movement_cb(self):
        pass

    def combat_results(self, combat_results):
        pass

    def end_game_cb(self):
        self._ended = True


class TestGamePlayer(unittest.TestCase):
    def test_play_requires_cpu_players(self):
        board = Board(2, 2)
        fac = Faction(id=str(uuid.uuid4()), name="F", color="red")
        player = Player(name="P", type=PlayerType.HUMAN, factions=[fac])
        game = Game([player], board)
        gp = GamePlayer(game)
        with self.assertRaises(ValueError):
            gp.play()

    def test_play_until_one_player_left(self):
        board = Board(2, 2)
        red_faction = Faction(id=str(uuid.uuid4()), name="Red", color="red")
        blue_faction = Faction(id=str(uuid.uuid4()), name="Blue", color="blue")

        red_player = DummyCPUPlayer("Red", [red_faction])
        blue_player = DummyCPUPlayer("Blue", [blue_faction])

        red_unit = Unit(
            str(uuid.uuid4()), "R", red_faction, red_player, "I", 1, 1, 1
        )
        blue_unit = Unit(
            str(uuid.uuid4()), "B", blue_faction, blue_player, "I", 1, 1, 1
        )
        board.add_unit(red_unit, 0, 0)
        board.add_unit(blue_unit, 0, 1)

        game = Game([red_player, blue_player], board)
        gp = GamePlayer(game)

        class StubCombat:
            instances = 0

            def __init__(self, game_obj):
                self.game = game_obj

            def resolve_combat(self):
                StubCombat.instances += 1
                units_to_remove = [
                    u for u in self.game.get_board().get_units()
                    if u.player == blue_player
                ]
                self.game.get_board().remove_units(units_to_remove)
                return MagicMock()

        with patch("battle_hexes_core.game.gameplayer.Combat", StubCombat):
            gp.play()

        units = game.get_board().get_units()
        self.assertEqual(len(units), 1)
        self.assertIs(units[0], red_unit)
        self.assertEqual(StubCombat.instances, 1)
        self.assertTrue(red_player._ended)
        self.assertTrue(blue_player._ended)

    def test_play_respects_max_turns(self):
        board = Board(2, 2)
        red_faction = Faction(id=str(uuid.uuid4()), name="Red", color="red")
        blue_faction = Faction(id=str(uuid.uuid4()), name="Blue", color="blue")

        red_player = DummyCPUPlayer("Red", [red_faction])
        blue_player = DummyCPUPlayer("Blue", [blue_faction])

        red_unit = Unit(
            str(uuid.uuid4()), "R", red_faction, red_player, "I", 1, 1, 1
        )
        blue_unit = Unit(
            str(uuid.uuid4()), "B", blue_faction, blue_player, "I", 1, 1, 1
        )
        board.add_unit(red_unit, 0, 0)
        board.add_unit(blue_unit, 0, 1)

        game = Game([red_player, blue_player], board)
        gp = GamePlayer(game)

        class StubCombat:
            instances = 0

            def __init__(self, game_obj):
                self.game = game_obj

            def resolve_combat(self):
                StubCombat.instances += 1
                return MagicMock()

        with patch("battle_hexes_core.game.gameplayer.Combat", StubCombat):
            gp.play(max_turns=3)

        self.assertEqual(StubCombat.instances, 3)
        units = game.get_board().get_units()
        self.assertEqual(len(units), 2)
        self.assertFalse(game.is_game_over())
        self.assertTrue(red_player._ended)
        self.assertTrue(blue_player._ended)
