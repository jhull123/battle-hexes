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
            no_retreat: Optional[Sequence['Unit']] = None,
    ):
        self.odds = odds
        self.die_roll = die_roll
        self.combat_result = combat_result
        self._battle_participants: Optional[
            Tuple[Tuple['Unit', ...], Tuple['Unit', ...]]
        ] = None
        self._no_retreat: tuple['Unit', ...] = ()
        if battle_participants is not None:
            self.set_battle_participants(battle_participants)
        if no_retreat is not None:
            self.set_no_retreat_units(no_retreat)

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

    def set_no_retreat_units(self, units: Sequence['Unit']) -> None:
        self._no_retreat = tuple(units)

    def add_no_retreat_units(self, units: Sequence['Unit']) -> None:
        combined = list(self._no_retreat)
        for unit in units:
            if unit not in combined:
                combined.append(unit)
        self._no_retreat = tuple(combined)

    def get_no_retreat_units(self) -> Tuple['Unit', ...]:
        return self._no_retreat

    def to_schema(self):
        return CombatResultSchema(
            combat_result_code=self.combat_result.name,
            combat_result_text=self.combat_result.value,
            odds=self.odds,
            die_roll=self.die_roll,
            no_retreat_unit_ids=tuple(
                str(unit.get_id()) for unit in self._no_retreat
            ),
        )


class CombatResultSchema(BaseModel):
    combat_result_code: str
    combat_result_text: str
    odds: Tuple[int, int]
    die_roll: int
    no_retreat_unit_ids: Tuple[str, ...] = ()
