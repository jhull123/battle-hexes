from enum import Enum
from typing import Optional, Sequence, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from battle_hexes_core.unit.unit import Unit
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
            combat_result: CombatResult,
            battle_participants: Optional[
                Tuple[
                    Sequence['Unit'],
                    Sequence['Unit'],
                ]
            ] = None,
    ):
        self.odds = odds
        self.die_roll = die_roll
        self.combat_result = combat_result
        self._battle_participants: Optional[
            Tuple[Tuple['Unit', ...], Tuple['Unit', ...]]
        ] = None
        if battle_participants is not None:
            self.set_battle_participants(battle_participants)

    def get_odds(self) -> tuple:
        return self.odds

    def get_die_roll(self) -> int:
        return self.die_roll

    def get_combat_result(self) -> CombatResult:
        return self.combat_result

    def set_battle_participants(
            self,
            battle_participants: Tuple[
                Sequence['Unit'],
                Sequence['Unit'],
            ]
    ) -> None:
        attackers, defenders = battle_participants
        self._battle_participants = (
            tuple(attackers),
            tuple(defenders),
        )

    def get_battle_participants(
            self,
    ) -> Optional[Tuple[Tuple['Unit', ...], Tuple['Unit', ...]]]:
        return self._battle_participants

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
