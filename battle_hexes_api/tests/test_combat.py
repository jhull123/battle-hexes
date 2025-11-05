import unittest

from battle_hexes_api.schemas import CombatResultSchema
from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


class TestCombatResultSchema(unittest.TestCase):
    def test_from_combat_result_data(self):
        faction = Faction(id="f4", name="Faction 4", color="#00ffff")
        player = Player(
            name="Dana",
            type=PlayerType.HUMAN,
            factions=[faction],
        )
        unit = Unit(
            id="u4",
            name="Unit 4",
            faction=faction,
            player=player,
            type="Infantry",
            attack=5,
            defense=3,
            move=2,
        )
        combat_data = CombatResultData(
            odds=(3, 2),
            die_roll=4,
            combat_result=CombatResult.DEFENDER_ELIMINATED,
            no_retreat=[unit],
        )

        schema = CombatResultSchema.from_combat_result_data(combat_data)

        self.assertEqual(schema.combat_result_code, "DEFENDER_ELIMINATED")
        self.assertEqual(schema.combat_result_text, "Defender Eliminated")
        self.assertEqual(schema.odds, (3, 2))
        self.assertEqual(schema.die_roll, 4)
        self.assertEqual(schema.no_retreat_unit_ids, ("u4",))
