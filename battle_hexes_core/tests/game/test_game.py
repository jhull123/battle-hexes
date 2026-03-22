import unittest
from unittest.mock import patch

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


RANDOM_PATCH_TARGET = (
    "battle_hexes_core.defensivefire.defensive_fire_resolver.random.random"
)


class TestGame(unittest.TestCase):

    def _make_two_player_game(self):
        board = Board(5, 5)
        faction1 = Faction(id="f1", name="f1", color="#fff")
        faction2 = Faction(id="f2", name="f2", color="#000")
        player1 = Player(name="P1", type=PlayerType.HUMAN, factions=[faction1])
        player2 = Player(name="P2", type=PlayerType.CPU, factions=[faction2])
        game = Game([player1, player2], board)
        game.set_defensive_fire_settings(
            type('Cfg', (), {
                'base_probability': 1.0,
                'minimum': 0.0,
                'maximum': 1.0,
            })()
        )
        return board, player1, player2, faction1, faction2, game

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

    def test_next_player_snapshots_defensive_fire_for_previous_player(self):
        board = Board(5, 5)
        faction1 = Faction(id="f1", name="f1", color="#fff")
        faction2 = Faction(id="f2", name="f2", color="#000")
        player1 = Player(
            name="P1",
            type=PlayerType.HUMAN,
            factions=[faction1],
        )
        player2 = Player(
            name="P2",
            type=PlayerType.CPU,
            factions=[faction2],
        )
        unit1 = Unit(
            id="u1",
            name="U1",
            faction=faction1,
            player=player1,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        unit2 = Unit(
            id="u2",
            name="U2",
            faction=faction2,
            player=player2,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        board.add_unit(unit1, 0, 0)
        board.add_unit(unit2, 4, 4)
        game = Game([player1, player2], board)

        game.next_player()

        self.assertTrue(unit1.has_defensive_fire(game.get_current_player()))
        self.assertFalse(unit2.has_defensive_fire(game.get_current_player()))

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

    def test_next_player_makes_unit_ineligible_with_one_move_remaining(self):
        board = Board(5, 5)
        faction1 = Faction(id="f1", name="f", color="#fff")
        faction2 = Faction(id="f2", name="e", color="#000")
        player1 = Player(name="P1", type=PlayerType.CPU, factions=[faction1])
        player2 = Player(name="P2", type=PlayerType.CPU, factions=[faction2])
        unit = Unit(
            id="u1",
            name="U",
            faction=faction1,
            player=player1,
            type="Infantry",
            attack=1,
            defense=1,
            move=2,
        )
        board.add_unit(unit, 0, 0)
        game = Game([player1, player2], board)

        start_hex = board.get_hex(0, 0)
        end_hex = board.get_hex(0, 1)
        plan = UnitMovementPlan(unit, [start_hex, end_hex])
        game.apply_movement_plans([plan])

        game.next_player()

        self.assertFalse(
            unit.has_defensive_fire(game.get_current_player())
        )

    def test_next_player_keeps_zero_move_unit_eligible(self):
        board = Board(5, 5)
        faction1 = Faction(id="f1", name="f", color="#fff")
        faction2 = Faction(id="f2", name="e", color="#000")
        player1 = Player(name="P1", type=PlayerType.CPU, factions=[faction1])
        player2 = Player(name="P2", type=PlayerType.CPU, factions=[faction2])
        unit = Unit(
            id="u1",
            name="Bunker",
            faction=faction1,
            player=player1,
            type="Infantry",
            attack=1,
            defense=1,
            move=0,
        )
        board.add_unit(unit, 0, 0)
        game = Game([player1, player2], board)

        game.next_player()

        self.assertTrue(
            unit.has_defensive_fire(game.get_current_player())
        )

    def test_next_player_clears_spent_state_for_new_current_player(self):
        board = Board(5, 5)
        faction1 = Faction(id="f1", name="f1", color="#fff")
        faction2 = Faction(id="f2", name="f2", color="#000")
        player1 = Player(
            name="P1",
            type=PlayerType.HUMAN,
            factions=[faction1],
        )
        player2 = Player(
            name="P2",
            type=PlayerType.CPU,
            factions=[faction2],
        )
        unit1 = Unit(
            id="u1",
            name="U1",
            faction=faction1,
            player=player1,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        unit2 = Unit(
            id="u2",
            name="U2",
            faction=faction2,
            player=player2,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        board.add_unit(unit1, 0, 0)
        board.add_unit(unit2, 4, 4)
        game = Game([player1, player2], board)

        unit2.record_friendly_turn_end(3, player1)
        unit2.spend_defensive_fire(player1)

        game.next_player()

        self.assertFalse(unit2.defensive_fire_spent_this_off_turn)
        self.assertFalse(unit2.has_defensive_fire(game.get_current_player()))

    def test_game_over_when_turn_limit_reached(self):
        board = Board(5, 5)
        game = Game([], board, turn_limit=1)
        game.turn_number = 2

        self.assertTrue(game.is_game_over())

    @patch(
        RANDOM_PATCH_TARGET,
        return_value=0.0,
    )
    def test_apply_movement_plans_triggers_defensive_fire_on_new_adjacency(
        self,
        _mock_random,
    ):
        board, player1, player2, faction1, faction2, game = (
            self._make_two_player_game()
        )
        mover = Unit(
            id="mover",
            name="Mover",
            faction=faction1,
            player=player1,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        defender = Unit(
            id="defender",
            name="Defender",
            faction=faction2,
            player=player2,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        board.add_unit(mover, 0, 0)
        board.add_unit(defender, 1, 2)
        defender.record_friendly_turn_end(defender.get_move(), player1)

        plan = UnitMovementPlan(
            mover,
            [board.get_hex(0, 0), board.get_hex(0, 1), board.get_hex(0, 2)],
        )

        result = game.apply_movement_plans([plan])

        self.assertEqual(mover.get_coords(), (0, 0))
        self.assertEqual(mover.current_turn_movement_points_remaining, 0)
        self.assertEqual(len(result.defensive_fire_results), 1)
        self.assertEqual(
            result.defensive_fire_results[0].outcome,
            "retreat",
        )
        self.assertFalse(
            defender.has_defensive_fire(game.get_current_player())
        )

    @patch(
        RANDOM_PATCH_TARGET,
        return_value=0.0,
    )
    def test_apply_movement_plans_does_not_trigger_when_already_adjacent(
        self,
        _mock_random,
    ):
        board, player1, player2, faction1, faction2, game = (
            self._make_two_player_game()
        )
        mover = Unit(
            id="mover",
            name="Mover",
            faction=faction1,
            player=player1,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        defender = Unit(
            id="defender",
            name="Defender",
            faction=faction2,
            player=player2,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        board.add_unit(mover, 0, 1)
        board.add_unit(defender, 1, 2)
        defender.record_friendly_turn_end(defender.get_move(), player1)

        plan = UnitMovementPlan(
            mover,
            [board.get_hex(0, 1), board.get_hex(0, 2)],
        )

        result = game.apply_movement_plans([plan])

        self.assertEqual(mover.get_coords(), (0, 2))
        self.assertEqual(len(result.defensive_fire_results), 0)
        self.assertTrue(defender.has_defensive_fire(game.get_current_player()))

    @patch(
        RANDOM_PATCH_TARGET,
        side_effect=[1.0, 0.0],
    )
    def test_defensive_fire_spent_once_per_off_turn(self, _mock_random):
        board, player1, player2, faction1, faction2, game = (
            self._make_two_player_game()
        )
        mover1 = Unit("m1", "Mover1", faction1, player1, "Infantry", 1, 1, 3)
        mover2 = Unit("m2", "Mover2", faction1, player1, "Infantry", 1, 1, 3)
        defender = Unit(
            id="defender",
            name="Defender",
            faction=faction2,
            player=player2,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        board.add_unit(mover1, 0, 0)
        board.add_unit(mover2, 2, 0)
        board.add_unit(defender, 1, 2)
        defender.record_friendly_turn_end(defender.get_move(), player1)

        result1 = game.apply_movement_plans([
            UnitMovementPlan(
                mover1,
                [board.get_hex(0, 0), board.get_hex(0, 1)],
            )
        ])
        result2 = game.apply_movement_plans([
            UnitMovementPlan(
                mover2,
                [board.get_hex(2, 0), board.get_hex(1, 1)],
            )
        ])

        self.assertEqual(len(result1.defensive_fire_results), 1)
        self.assertEqual(
            result1.defensive_fire_results[0].outcome,
            "no_effect",
        )
        self.assertEqual(len(result2.defensive_fire_results), 0)
        self.assertFalse(
            defender.has_defensive_fire(game.get_current_player())
        )

    @patch(
        RANDOM_PATCH_TARGET,
        side_effect=[1.0, 0.0],
    )
    def test_multiple_defenders_resolve_in_deterministic_order(
        self,
        _mock_random,
    ):
        board, player1, player2, faction1, faction2, game = (
            self._make_two_player_game()
        )
        mover = Unit(
            "mover", "Mover", faction1, player1, "Infantry", 1, 1, 3
        )
        defender_b = Unit(
            "b", "Defender B", faction2, player2, "Infantry", 1, 1, 3
        )
        defender_a = Unit(
            "a", "Defender A", faction2, player2, "Infantry", 1, 1, 3
        )
        board.add_unit(mover, 0, 0)
        board.add_unit(defender_b, 1, 2)
        board.add_unit(defender_a, 0, 2)
        defender_a.record_friendly_turn_end(defender_a.get_move(), player1)
        defender_b.record_friendly_turn_end(defender_b.get_move(), player1)

        result = game.apply_movement_plans([
            UnitMovementPlan(
                mover,
                [board.get_hex(0, 0), board.get_hex(0, 1)],
            )
        ])

        self.assertEqual(
            [entry.firing_unit_id for entry in result.defensive_fire_results],
            ["a", "b"],
        )
        self.assertEqual(mover.get_coords(), (0, 0))

    @patch(
        RANDOM_PATCH_TARGET,
        return_value=1.0,
    )
    def test_defensive_fire_no_effect_leaves_position_unchanged(
        self,
        _mock_random,
    ):
        board, player1, player2, faction1, faction2, game = (
            self._make_two_player_game()
        )
        game.set_defensive_fire_settings(
            type('Cfg', (), {
                'base_probability': 0.5,
                'minimum': 0.0,
                'maximum': 1.0,
            })()
        )
        mover = Unit(
            "mover", "Mover", faction1, player1, "Infantry", 1, 1, 3
        )
        defender = Unit(
            "defender",
            "Defender",
            faction2,
            player2,
            "Infantry",
            1,
            1,
            3,
        )
        board.add_unit(mover, 0, 0)
        board.add_unit(defender, 1, 2)
        defender.record_friendly_turn_end(defender.get_move(), player1)

        result = game.apply_movement_plans([
            UnitMovementPlan(
                mover,
                [
                    board.get_hex(0, 0),
                    board.get_hex(0, 1),
                    board.get_hex(0, 2),
                ],
            )
        ])

        self.assertEqual(mover.get_coords(), (0, 1))
        self.assertEqual(result.defensive_fire_results[0].outcome, "no_effect")

    @patch(
        RANDOM_PATCH_TARGET,
        return_value=0.2,
    )
    def test_defensive_fire_probability_uses_terrain_modifier_and_clamp(
        self,
        _mock_random,
    ):
        board, player1, player2, faction1, faction2, game = (
            self._make_two_player_game()
        )
        game.set_defensive_fire_settings(
            type('Cfg', (), {
                'base_probability': 0.5,
                'minimum': 0.1,
                'maximum': 0.3,
            })()
        )
        board.get_hex(0, 1).set_terrain(type('Terrain', (), {
            'defensive_fire_modifier': 10.0,
            'move_cost': 1,
        })())
        mover = Unit(
            "mover", "Mover", faction1, player1, "Infantry", 1, 1, 3
        )
        defender = Unit(
            "defender",
            "Defender",
            faction2,
            player2,
            "Infantry",
            1,
            1,
            3,
        )
        defender.defensive_fire_modifier = 2.0
        board.add_unit(mover, 0, 0)
        board.add_unit(defender, 1, 2)
        defender.record_friendly_turn_end(defender.get_move(), player1)

        result = game.apply_movement_plans([
            UnitMovementPlan(
                mover,
                [board.get_hex(0, 0), board.get_hex(0, 1)],
            )
        ])

        self.assertEqual(result.defensive_fire_results[0].probability, 0.3)
        self.assertEqual(result.defensive_fire_results[0].outcome, "retreat")
