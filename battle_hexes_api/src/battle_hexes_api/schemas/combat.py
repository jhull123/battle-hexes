"""Schemas describing combat results."""

from __future__ import annotations

from typing import Tuple

from pydantic import BaseModel

from battle_hexes_core.combat.combatresult import CombatResultData


class CombatResultSchema(BaseModel):
    """API representation of a single combat resolution."""

    combat_result_code: str
    combat_result_text: str
    odds: Tuple[int, int]
    die_roll: int
    no_retreat_unit_ids: Tuple[str, ...] = ()

    @classmethod
    def from_combat_result_data(
        cls,
        combat_result_data: CombatResultData,
    ) -> "CombatResultSchema":
        """Create a schema from a :class:`CombatResultData` instance."""

        return cls(
            combat_result_code=combat_result_data.get_combat_result().name,
            combat_result_text=combat_result_data.get_combat_result().value,
            odds=tuple(combat_result_data.get_odds()),
            die_roll=combat_result_data.get_die_roll(),
            no_retreat_unit_ids=tuple(
                str(unit.get_id())
                for unit in combat_result_data.get_no_retreat_units()
            ),
        )
