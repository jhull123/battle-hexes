import unittest

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestGame(unittest.TestCase):
    def test_game_id_is_unique(self):
        game1 = Game([], Board(5, 5))
        game2 = Game([], Board(5, 5))
        self.assertNotEqual(game1.get_id(), game2.get_id(),
                            "Game IDs should be unique")

    def test_game_board_is_initialized(self):
        board = Board(5, 5)
        game = Game([], board)
        self.assertIs(game.get_board(), board,
                      "Game board should be initialized")

    def test_next_player_cycles_through_players(self):
        # Create mock players
        class MockPlayer:
            def __init__(self, name):
                self.name = name
                self.factions = []

            def owns(self, unit):
                return False

            def __eq__(self, other):
                return isinstance(other, MockPlayer) and \
                    self.name == other.name

        player1 = MockPlayer("Alice")
        player2 = MockPlayer("Bob")
        player3 = MockPlayer("Charlie")
        board = Board(5, 5)
        game = Game([player1, player2, player3], board)

        # Initial current player should be player1
        self.assertEqual(game.get_current_player(), player1)

        # Advance to next player
        next_player = game.next_player()
        self.assertEqual(next_player, player2)
        self.assertEqual(game.get_current_player(), player2)

        # Advance to next player
        next_player = game.next_player()
        self.assertEqual(next_player, player3)
        self.assertEqual(game.get_current_player(), player3)

        # Advance to next player (should cycle back to player1)
        next_player = game.next_player()
        self.assertEqual(next_player, player1)
        self.assertEqual(game.get_current_player(), player1)

    def test_next_player_restores_defensive_fire_for_previous_player(self):
        board = Board(5, 5)
        faction1 = Faction(id="f1", name="f1", color="#fff")
        faction2 = Faction(id="f2", name="f2", color="#000")
        player1 = Player(name="P1", type=PlayerType.HUMAN, factions=[faction1])
        player2 = Player(name="P2", type=PlayerType.CPU, factions=[faction2])
        unit1 = Unit(
            id="u1",
            name="U1",
            faction=faction1,
            player=player1,
            type="Infantry",
            attack=1,
            defense=1,
            move=1,
        )
        unit2 = Unit(
            id="u2",
            name="U2",
            faction=faction2,
            player=player2,
            type="Infantry",
            attack=1,
            defense=1,
            move=1,
        )
        board.add_unit(unit1, 0, 0)
        board.add_unit(unit2, 0, 1)
        unit1.set_defensive_fire_available(False)
        unit2.set_defensive_fire_available(False)
        game = Game([player1, player2], board)

        game.next_player()

        self.assertTrue(unit1.has_defensive_fire())
        self.assertFalse(unit2.has_defensive_fire())

    def test_next_player_with_no_players_returns_none(self):
        board = Board(5, 5)
        game = Game([], board)
        # next_player should return None if there are no players
        self.assertIsNone(game.next_player())

    def test_apply_movement_plans_updates_unit_coordinates(self):
        board = Board(5, 5)
        import uuid
        faction = Faction(id=str(uuid.uuid4()), name="f", color="#fff")
        player = Player(name="P", type=PlayerType.HUMAN, factions=[faction])
        unit = Unit(id=2, name="U", faction=faction, player=player,
                    type="Infantry", attack=1, defense=1, move=1)
        board.add_unit(unit, 0, 0)
        game = Game([player], board)

        start_hex = board.get_hex(0, 0)
        end_hex = board.get_hex(0, 1)
        plan = UnitMovementPlan(unit, [start_hex, end_hex])

        game.apply_movement_plans([plan])

        self.assertEqual(unit.get_coords(), (0, 1))

    def test_apply_movement_plans_removes_defensive_fire_at_one_move_left(
        self
    ):
        board = Board(5, 5)
        faction = Faction(id="f1", name="f", color="#fff")
        player = Player(name="P", type=PlayerType.CPU, factions=[faction])
        unit = Unit(
            id="u1",
            name="U",
            faction=faction,
            player=player,
            type="Infantry",
            attack=1,
            defense=1,
            move=2,
        )
        board.add_unit(unit, 0, 0)
        game = Game([player], board)

        start_hex = board.get_hex(0, 0)
        end_hex = board.get_hex(0, 1)
        plan = UnitMovementPlan(unit, [start_hex, end_hex])

        game.apply_movement_plans([plan])

        self.assertFalse(unit.has_defensive_fire())

    def test_apply_movement_plans_removes_defensive_fire_when_enemy_adjacent(
        self
    ):
        board = Board(5, 5)
        red_faction = Faction(id="red", name="Red", color="#fff")
        blue_faction = Faction(id="blue", name="Blue", color="#000")
        red_player = Player(
            name="Red",
            type=PlayerType.CPU,
            factions=[red_faction],
        )
        blue_player = Player(
            name="Blue",
            type=PlayerType.CPU,
            factions=[blue_faction],
        )
        moving_unit = Unit(
            id="u1",
            name="Mover",
            faction=red_faction,
            player=red_player,
            type="Infantry",
            attack=1,
            defense=1,
            move=4,
        )
        enemy_unit = Unit(
            id="u2",
            name="Enemy",
            faction=blue_faction,
            player=blue_player,
            type="Infantry",
            attack=1,
            defense=1,
            move=4,
        )
        board.add_unit(moving_unit, 0, 0)
        board.add_unit(enemy_unit, 1, 2)
        game = Game([red_player, blue_player], board)

        start_hex = board.get_hex(0, 0)
        end_hex = board.get_hex(0, 1)
        plan = UnitMovementPlan(moving_unit, [start_hex, end_hex])

        game.apply_movement_plans([plan])

        self.assertFalse(moving_unit.has_defensive_fire())

    def test_apply_movement_plans_keeps_defensive_fire_for_zero_move_unit(
        self
    ):
        board = Board(5, 5)
        faction = Faction(id="f1", name="f", color="#fff")
        player = Player(name="P", type=PlayerType.CPU, factions=[faction])
        unit = Unit(
            id="u1",
            name="Bunker",
            faction=faction,
            player=player,
            type="Infantry",
            attack=1,
            defense=1,
            move=0,
        )
        board.add_unit(unit, 0, 0)
        game = Game([player], board)

        start_hex = board.get_hex(0, 0)
        plan = UnitMovementPlan(unit, [start_hex])

        game.apply_movement_plans([plan])

        self.assertTrue(unit.has_defensive_fire())

    def test_game_over_when_turn_limit_reached(self):
        board = Board(5, 5)
        game = Game([], board, turn_limit=1)
        game.turn_number = 2

        self.assertTrue(game.is_game_over())
