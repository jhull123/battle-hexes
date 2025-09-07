from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.combat.combatresults import CombatResults


def test_combat_results_stores_data() -> None:
    results = CombatResults()
    data = CombatResultData((1, 1), 2, CombatResult.DEFENDER_ELIMINATED)
    results.add_battle(data)
    assert results.get_battles() == [data]
