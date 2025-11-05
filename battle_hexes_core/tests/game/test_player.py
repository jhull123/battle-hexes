import unittest

from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction


class TestPlayer(unittest.TestCase):
    def test_movement_not_implemented(self):
        player = Player(name='P1', type=PlayerType.HUMAN, factions=[])
        with self.assertRaises(NotImplementedError):
            player.movement()

    def test_owns_and_own_units(self):
        faction = Faction(id="alpha", name="Alpha", color="#ff0000")
        other_faction = Faction(id="beta", name="Beta", color="#00ff00")
        player = Player(
            name="Commander",
            type=PlayerType.HUMAN,
            factions=[faction],
        )

        owned_unit = type("Unit", (), {"faction": faction})()
        enemy_unit = type("Unit", (), {"faction": other_faction})()

        self.assertTrue(player.owns(owned_unit))
        self.assertFalse(player.owns(enemy_unit))
        self.assertEqual(
            [owned_unit],
            player.own_units([owned_unit, enemy_unit]),
        )

    def test_factions_iterable_is_copied(self):
        faction = Faction(id="gamma", name="Gamma", color="#0000ff")
        player = Player(
            name="Strategist",
            type=PlayerType.CPU,
            factions=(faction,),
        )

        self.assertEqual([faction], player.factions)
        self.assertIsInstance(player.factions, list)

    def test_player_factions_are_independent_from_source(self):
        faction = Faction(id="delta", name="Delta", color="#ffff00")
        other_faction = Faction(id="epsilon", name="Epsilon", color="#123456")
        factions = [faction]
        player = Player(
            name="Tactician",
            type=PlayerType.HUMAN,
            factions=factions,
        )

        self.assertIsNot(player.factions, factions)

        player.factions.append(other_faction)
        self.assertEqual([faction], factions)

        factions.append(other_faction)
        self.assertEqual([faction, other_faction], factions)
        self.assertEqual([faction, other_faction], player.factions)
