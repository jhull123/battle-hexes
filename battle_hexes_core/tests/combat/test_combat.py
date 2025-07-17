import unittest
import uuid
from game.board import Board
from game.game import Game
from game.player import Player, PlayerType
from combat.combat import Combat
from combat.combatresult import CombatResult
from unit.faction import Faction
from unit.unit import Unit


class TestCombat(unittest.TestCase):
    def setUp(self):
        self.red_faction = Faction(id=uuid.uuid4(), name='Red', color='red')
        self.blue_faction = Faction(id=uuid.uuid4(), name='Blue', color='blue')

        self.red_player = Player(
            name='Red Player',
            type=PlayerType.HUMAN,
            factions=[self.red_faction]
        )
        self.blue_player = Player(
            name='Blue Player',
            type=PlayerType.CPU,
            factions=[self.blue_faction]
        )

        self.board = Board(10, 10)
        self.game = Game([self.red_player, self.blue_player], self.board)
        self.combat = Combat(self.game)

        self.red_unit = Unit(id=uuid.uuid4(), name='Red Unit',
                             faction=self.red_faction,
                             player=self.red_player,
                             type='Infantry',
                             attack=4, defense=4, move=4)
        self.blue_unit = Unit(id=uuid.uuid4(), name='Blue Unit',
                              faction=self.blue_faction,
                              player=self.blue_player,
                              type='Recon',
                              attack=2, defense=2, move=6)

    def test_results_empty_when_empty_board(self):
        combat_result = self.combat.resolve_combat()
        self.assertEqual(0, len(combat_result.get_battles()))

    def test_results_empty_when_no_combat(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 3, 5)
        combat_result = self.combat.resolve_combat()
        self.assertEqual(0, len(combat_result.get_battles()))

    def test_board_is_unchanged_when_no_combat(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 3, 5)

        self.combat.resolve_combat()

        self.assertEqual((6, 4), self.red_unit.get_coords())
        self.assertEqual((3, 5), self.blue_unit.get_coords())

    def test_board_one_battle(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 6, 5)
        self.combat.set_static_die_roll(6)

        combat_results = self.combat.resolve_combat()
        battles = combat_results.get_battles()

        self.assertEqual(1, len(battles))

    def test_board_attacker_elim_leaves_one_unit_on_the_board(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 6, 5)
        self.combat.set_static_die_roll(6)

        self.combat.resolve_combat()

        self.assertEqual(1, len(self.board.get_units()))
        self.assertEqual(self.blue_unit, self.board.get_units()[0])

    def test_board_attacker_elim_has_correct_combat_data(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 6, 5)
        self.combat.set_static_die_roll(6)

        combat_result = self.combat.resolve_combat().get_battles()[0]

        self.assertEqual((2, 1), combat_result.get_odds())
        self.assertEqual(6, combat_result.get_die_roll())
        self.assertEqual(
            CombatResult.ATTACKER_ELIMINATED,
            combat_result.get_combat_result()
        )

    def test_board_defender_elim_leaves_one_unit_on_the_board(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 5, 5)
        self.combat.set_static_die_roll(1)

        self.combat.resolve_combat()

        self.assertEqual(1, len(self.board.get_units()))
        self.assertEqual(self.red_unit, self.board.get_units()[0])

    def test_exchange_leaves_board_empty(self):
        self.board.add_unit(self.red_unit, 6, 4)
        self.board.add_unit(self.blue_unit, 5, 3)
        self.combat.set_static_die_roll(2)

        self.combat.resolve_combat()

        self.assertEqual(0, len(self.board.get_units()))

    def test_a_back_2_from_lower_left_moves_attacker(self):
        self.board.add_unit(self.red_unit, 4, 4)
        self.board.add_unit(self.blue_unit, 3, 5)
        self.combat.set_static_die_roll(4)

        self.combat.resolve_combat()

        self.assertEqual(2, len(self.board.get_units()))
        self.assertEqual((5, 2), self.red_unit.get_coords())

    def test_a_back_2_from_upper_right_moves_attacker(self):
        self.board.add_unit(self.red_unit, 3, 6)
        self.board.add_unit(self.blue_unit, 3, 5)
        self.combat.set_static_die_roll(4)

        self.combat.resolve_combat()

        self.assertEqual(2, len(self.board.get_units()))
        self.assertEqual((2, 8), self.red_unit.get_coords())

    def test_d_back_2_from_above_moves_defender(self):
        self.board.add_unit(self.red_unit, 2, 5)
        self.board.add_unit(self.blue_unit, 3, 5)
        self.combat.set_static_die_roll(3)

        self.combat.resolve_combat()

        self.assertEqual(2, len(self.board.get_units()))
        self.assertEqual((5, 5), self.blue_unit.get_coords())

    def test_defender_retreat_off_map_eliminates_unit(self):
        self.board.add_unit(self.red_unit, 0, 1)
        self.board.add_unit(self.blue_unit, 0, 0)
        self.combat.set_static_die_roll(3)

        self.combat.resolve_combat()

        self.assertEqual(1, len(self.board.get_units()))
        self.assertEqual(self.red_unit, self.board.get_units()[0])
