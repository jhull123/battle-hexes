import logging
import random
from math import gcd

from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)


logger = logging.getLogger(__name__)


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

    def shift_odds(
        self,
        odds: tuple[int, int],
        combat_odds_shift: int,
    ) -> tuple:
        try:
            base_index = CombatSolver.STANDARD_ODDS.index(odds)
        except ValueError as exc:
            raise ValueError(f"Unknown odds column: {odds}") from exc

        max_index = len(CombatSolver.STANDARD_ODDS) - 1
        shifted_index = base_index + combat_odds_shift
        final_index = min(max(shifted_index, 0), max_index)
        return CombatSolver.STANDARD_ODDS[final_index]

    def solve_combat(
            self,
            attack_factor: int,
            defense_factor: int,
            combat_odds_shift: int = 0,
    ) -> CombatResultData:
        base_odds = self.get_odds(attack_factor, defense_factor)
        final_odds = self.shift_odds(base_odds, combat_odds_shift)
        odds_label = f'{final_odds[0]}:{final_odds[1]}'
        logger.info(
            "Resolving combat with %s against %s at base odds %s, "
            "shift %s, final odds %s",
            attack_factor,
            defense_factor,
            f'{base_odds[0]}:{base_odds[1]}',
            combat_odds_shift,
            odds_label,
        )

        if odds_label == '1:7':
            return CombatResultData(
                final_odds,
                -1,
                CombatResult.ATTACKER_ELIMINATED,
                base_odds=base_odds,
                final_odds=final_odds,
            )
        if odds_label == '7:1':
            return CombatResultData(
                final_odds,
                -1,
                CombatResult.DEFENDER_ELIMINATED,
                base_odds=base_odds,
                final_odds=final_odds,
            )

        die_roll = self._roll_die()
        combat_result = CombatSolver.RESULTS_TABLE[odds_label][die_roll - 1]
        return CombatResultData(
            final_odds,
            die_roll,
            combat_result,
            base_odds=base_odds,
            final_odds=final_odds,
        )

    def set_static_die_roll(self, static_roll: int):
        self.static_die_roll = static_roll

    def _roll_die(self) -> int:
        if self.static_die_roll:
            return self.static_die_roll
        return random.randint(1, 6)
