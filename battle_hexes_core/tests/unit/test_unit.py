import unittest
import uuid
from battle_hexes_core.game.board import Board
from battle_hexes_core.unit.unit import Unit
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.faction1 = Faction(
            id=str(uuid.uuid4()), name="Faction1", color="Red"
        )
        self.faction2 = Faction(
            id=str(uuid.uuid4()), name="Faction2", color="Blue"
        )
        self.player1 = Player(
            name="Player1",
            type=PlayerType.CPU,
            factions=[self.faction1]
        )
        self.player2 = Player(
            name="Player2",
            type=PlayerType.CPU,
            factions=[self.faction2]
        )

        self.unit1 = Unit(
            id=str(uuid.uuid4()),
            name="Unit1",
            player=self.player1,
            faction=self.faction1,
            type="Infantry",
            attack=10,
            defense=5,
            move=3,
            row=0,
            column=0
        )

        self.unit2 = Unit(
            id=str(uuid.uuid4()),
            name="Unit2",
            player=self.player1,
            faction=self.faction1,
            type="Cavalry",
            attack=12,
            defense=6,
            move=4,
            row=1,
            column=1
        )

        self.unit3 = Unit(
            id=str(uuid.uuid4()),
            name="Unit3",
            player=self.player2,
            faction=self.faction2,
            type="Archer",
            attack=8,
            defense=4,
            move=2,
            row=2,
            column=2
        )

    def test_is_friendly_same_player(self):
        self.assertTrue(self.unit1.is_friendly(self.unit2))

    def test_is_friendly_different_player(self):
        self.assertFalse(self.unit1.is_friendly(self.unit3))

    def test_forced_move_success(self):
        board = Board(6, 6)
        board.add_unit(self.unit1, 2, 2)
        board.add_unit(self.unit3, 2, 3)

        result = self.unit1.forced_move(board, self.unit3.get_coords(), 2)

        self.assertTrue(result)
        self.assertEqual((1, 0), self.unit1.get_coords())

    def test_forced_move_blocked_restores_position(self):
        board = Board(6, 6)
        board.add_unit(self.unit1, 2, 2)

        enemy = Unit(
            id=str(uuid.uuid4()),
            name="Enemy",
            player=self.player2,
            faction=self.faction2,
            type="Infantry",
            attack=5,
            defense=5,
            move=3,
        )
        blocker = Unit(
            id=str(uuid.uuid4()),
            name="Blocker",
            player=self.player2,
            faction=self.faction2,
            type="Infantry",
            attack=5,
            defense=5,
            move=3,
        )
        board.add_unit(enemy, 2, 3)
        board.add_unit(blocker, 1, 0)

        result = self.unit1.forced_move(board, enemy.get_coords(), 2)

        self.assertFalse(result)
        self.assertEqual((2, 2), self.unit1.get_coords())

    def test_forced_move_blocked_when_destination_exceeds_stacking_limit(self):
        board = Board(6, 6)
        board.set_stacking_limit(1)
        board.add_unit(self.unit1, 2, 2)

        enemy = Unit(
            id=str(uuid.uuid4()),
            name="Enemy",
            player=self.player2,
            faction=self.faction2,
            type="Infantry",
            attack=5,
            defense=5,
            move=3,
        )
        friendly_blocker = Unit(
            id=str(uuid.uuid4()),
            name="Friendly Blocker",
            player=self.player1,
            faction=self.faction1,
            type="Infantry",
            attack=5,
            defense=5,
            move=3,
        )
        board.add_unit(enemy, 2, 3)
        board.add_unit(friendly_blocker, 1, 1)

        result = self.unit1.forced_move(board, enemy.get_coords(), 1)

        self.assertFalse(result)
        self.assertEqual((2, 2), self.unit1.get_coords())

    def test_forced_move_blocked_when_intermediate_step_exceeds_stacking_limit(
        self,
    ):
        board = Board(6, 6)
        board.set_stacking_limit(1)
        board.add_unit(self.unit1, 2, 2)

        enemy = Unit(
            id=str(uuid.uuid4()),
            name="Enemy",
            player=self.player2,
            faction=self.faction2,
            type="Infantry",
            attack=5,
            defense=5,
            move=3,
        )
        intermediate_blocker = Unit(
            id=str(uuid.uuid4()),
            name="Intermediate Blocker",
            player=self.player1,
            faction=self.faction1,
            type="Infantry",
            attack=5,
            defense=5,
            move=3,
        )
        board.add_unit(enemy, 2, 3)
        board.add_unit(intermediate_blocker, 1, 1)

        result = self.unit1.forced_move(board, enemy.get_coords(), 2)

        self.assertFalse(result)
        self.assertEqual((2, 2), self.unit1.get_coords())

    def test_turn_end_needs_more_than_one_move_remaining(self):
        self.unit1.record_friendly_turn_end(1, self.player2)

        self.assertFalse(
            self.unit1.has_defensive_fire(self.player2)
        )

    def test_record_friendly_turn_end_allows_zero_move_unit(self):
        bunker = Unit(
            id=str(uuid.uuid4()),
            name="Bunker",
            player=self.player1,
            faction=self.faction1,
            type="Infantry",
            attack=1,
            defense=1,
            move=0,
            row=0,
            column=0,
        )

        bunker.record_friendly_turn_end(0, self.player2)

        self.assertTrue(bunker.has_defensive_fire(self.player2))

    def test_forced_retreat_revokes_defensive_fire_immediately(self):
        self.unit1.record_friendly_turn_end(3, self.player2)

        self.unit1.record_forced_retreat(self.player2)

        self.assertFalse(self.unit1.has_defensive_fire(self.player2))

    def test_spending_defensive_fire_marks_unit_unavailable_until_reset(self):
        self.unit1.record_friendly_turn_end(3, self.player2)

        self.unit1.spend_defensive_fire(self.player2)

        self.assertFalse(self.unit1.has_defensive_fire(self.player2))
        self.unit1.reset_defensive_fire_for_new_turn(self.player1)
        self.assertFalse(self.unit1.has_defensive_fire(self.player1))
        self.assertTrue(self.unit1.has_defensive_fire(self.player2))
