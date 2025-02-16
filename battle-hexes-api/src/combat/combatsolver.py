from src.combat.combatresult import CombatResult, CombatResultData
from math import gcd
import random


class CombatSolver:
    STANDARD_ODDS_RATIOS = (1/7, 1/6, 1/5, 1/4, 1/3, 1/2, 1, 2, 3, 4, 5, 6, 7)
    STANDARD_ODDS = (
        (1, 7),
        (1, 6),
        (1, 5),
        (1, 4),
        (1, 3),
        (1, 2),
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 1)
    )
    RESULTS_TABLE = {
        '1:6': (
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED
        ),
        '1:5': (
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED
        ),
        '1:4': (
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED
        ),
        '1:3': (
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED
        ),
        '1:2': (
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.EXCHANGE,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED
        ),
        '1:1': (
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.EXCHANGE,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.ATTACKER_ELIMINATED,
            CombatResult.ATTACKER_ELIMINATED
        ),
        '2:1': (
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.EXCHANGE,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.ATTACKER_RETREAT_2,
            CombatResult.EXCHANGE,
            CombatResult.ATTACKER_ELIMINATED
        ),
        '3:1': (
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.EXCHANGE,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.EXCHANGE,
            CombatResult.DEFENDER_ELIMINATED
        ),
        '4:1': (
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.EXCHANGE,
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.DEFENDER_ELIMINATED
        ),
        '5:1': (
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_ELIMINATED
        ),
        '6:1': (
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_RETREAT_2,
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_ELIMINATED,
            CombatResult.DEFENDER_ELIMINATED
        )
    }

    def __init__(self):
        self.static_die_roll = None

    def get_odds(self, attack_factor, defense_factor):
        gr_cmn_denom = gcd(attack_factor, defense_factor)
        ratio = (
            attack_factor // gr_cmn_denom
            ) / (
                defense_factor // gr_cmn_denom
            )
        closest_ratio_index = min(
            enumerate(CombatSolver.STANDARD_ODDS_RATIOS),
            key=lambda x: abs(ratio - x[1])
        )[0]
        return CombatSolver.STANDARD_ODDS[closest_ratio_index]

    def solve_combat(
            self,
            attack_factor: int,
            defense_factor: int
    ) -> CombatResultData:
        odds = self.get_odds(attack_factor, defense_factor)
        odds_label = f'{odds[0]}:{odds[1]}'

        if odds_label == '1:7':
            return CombatResultData(
                odds,
                -1,
                CombatResult.ATTACKER_ELIMINATED
            )
        if odds_label == '7:1':
            return CombatResultData(
                odds,
                -1,
                CombatResult.DEFENDER_ELIMINATED
            )

        die_roll = self._roll_die()
        combat_result = CombatSolver.RESULTS_TABLE[odds_label][die_roll - 1]
        return CombatResultData(odds, die_roll, combat_result)

    def set_static_die_roll(self, static_roll: int):
        self.static_die_roll = static_roll

    def _roll_die(self) -> int:
        if self.static_die_roll:
            return self.static_die_roll
        return random.randint(1, 6)
