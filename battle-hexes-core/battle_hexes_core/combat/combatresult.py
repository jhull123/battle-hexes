from enum import Enum
from typing import Tuple
from pydantic import BaseModel


class CombatResult(Enum):
    ATTACKER_ELIMINATED = 'Attacker Eliminated'
    ATTACKER_RETREAT_2 = 'Attacker Retreat 2 Hexes'
    DEFENDER_ELIMINATED = 'Defender Eliminated'
    DEFENDER_RETREAT_2 = 'Defender Retreat 2 Hexes'
    EXCHANGE = 'Exchange'


class CombatResultData:
    def __init__(
            self,
            odds: tuple,
            die_roll: int,
            combat_result: CombatResult):
        self.odds = odds
        self.die_roll = die_roll
        self.combat_result = combat_result

    def get_odds(self) -> tuple:
        return self.odds

    def get_die_roll(self) -> int:
        return self.die_roll

    def get_combat_result(self) -> CombatResult:
        return self.combat_result

    def to_schema(self):
        return CombatResultSchema(
            combat_result_code=self.combat_result.name,
            combat_result_text=self.combat_result.value,
            odds=self.odds,
            die_roll=self.die_roll
        )


class CombatResultSchema(BaseModel):
    combat_result_code: str
    combat_result_text: str
    odds: Tuple[int, int]
    die_roll: int
