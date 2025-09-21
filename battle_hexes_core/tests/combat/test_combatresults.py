from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.combat.combatresults import CombatResults


def test_combat_results_stores_data() -> None:
    results = CombatResults()
    attackers = (object(),)
    defenders = (object(),)
    data = CombatResultData(
        (1, 1),
        2,
        CombatResult.DEFENDER_ELIMINATED,
        (attackers, defenders),
    )
    results.add_battle(data)
    assert results.get_battles() == [data]
    assert data.get_battle_participants() == (attackers, defenders)
