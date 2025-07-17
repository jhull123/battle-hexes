import unittest
from combat.combatsolver import CombatSolver
from combat.combatresult import CombatResult


class TestCombatSolver(unittest.TestCase):
    def setUp(self):
        self.combat_solver = CombatSolver()

    def test_7_vs_2_is_2_to_1_odds(self):
        odds = self.combat_solver.get_odds(7, 3)
        assert odds == (2, 1), f"Expected (2, 1), but got {odds}"

    def test_11_vs_16_is_1_to_2_odds(self):
        odds = self.combat_solver.get_odds(11, 16)
        assert odds == (1, 2), f"Expected (1, 2), but got {odds}"

    def test_2_vs_4_is_1_to_2_odds(self):
        odds = self.combat_solver.get_odds(2, 4)
        self.assertEqual((1, 2), odds, f'Expected (1, 2) but got {odds}')

    def test_12_vs_5_combat(self):
        self.combat_solver.set_static_die_roll(5)
        combat_result = self.combat_solver.solve_combat(12, 5)
        assert combat_result.get_odds() == (2, 1)
        assert combat_result.get_die_roll() == 5
        assert combat_result.get_combat_result() == CombatResult.EXCHANGE

    def test_automatic_attack_elim(self):
        combat_result = self.combat_solver.solve_combat(1, 7)
        assert combat_result.get_odds() == (1, 7)
        assert combat_result.get_die_roll() == -1
        assert combat_result.get_combat_result() \
            == CombatResult.ATTACKER_ELIMINATED
