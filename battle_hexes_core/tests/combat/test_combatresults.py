import uuid

from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


def test_combat_results_stores_data() -> None:
    results = CombatResults()
    data = CombatResultData((1, 1), 2, CombatResult.DEFENDER_ELIMINATED)
    results.add_battle(data)
    assert results.get_battles() == [data]


def test_combat_result_data_tracks_participants() -> None:
    faction = Faction(id=uuid.uuid4(), name="Faction", color="red")
    player = Player(name="Player", type=PlayerType.CPU, factions=[faction])
    attacker = Unit(
        uuid.uuid4(),
        "Attacker",
        faction,
        player,
        "Inf",
        3,
        2,
        3,
    )
    defender = Unit(
        uuid.uuid4(),
        "Defender",
        faction,
        player,
        "Inf",
        2,
        3,
        3,
    )

    data = CombatResultData(
        (1, 1),
        3,
        CombatResult.DEFENDER_ELIMINATED,
        participants=((attacker,), (defender,)),
    )

    participants = data.get_participants()
    assert participants is not None
    attackers, defenders = participants
    assert attackers == (attacker,)
    assert defenders == (defender,)
