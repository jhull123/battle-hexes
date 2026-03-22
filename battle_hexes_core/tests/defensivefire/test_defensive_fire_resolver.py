import unittest
from unittest.mock import patch

from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)
from battle_hexes_core.defensivefire.defensive_fire_resolver import (
    DefensiveFireResolver,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


RANDOM_PATCH_TARGET = (
    "battle_hexes_core.defensivefire.defensive_fire_resolver.random.random"
)


class TestDefensiveFireResolver(unittest.TestCase):
    def setUp(self):
        self.board = Board(5, 5)
        self.faction1 = Faction(id="f1", name="f1", color="#fff")
        self.faction2 = Faction(id="f2", name="f2", color="#000")
        self.player1 = Player(
            name="P1",
            type=PlayerType.HUMAN,
            factions=[self.faction1],
        )
        self.player2 = Player(
            name="P2",
            type=PlayerType.CPU,
            factions=[self.faction2],
        )
        self.settings = DefensiveFireSettings(
            base_probability=1.0,
            minimum=0.0,
            maximum=1.0,
        )
        self.resolver = DefensiveFireResolver(self.board, self.settings)

    def _add_unit(self, unit_id, faction, player, row, column):
        unit = Unit(
            id=unit_id,
            name=unit_id,
            faction=faction,
            player=player,
            type="Infantry",
            attack=1,
            defense=1,
            move=3,
        )
        self.board.add_unit(unit, row, column)
        return unit

    @patch(
        RANDOM_PATCH_TARGET,
        return_value=0.0,
    )
    def test_resolve_defensive_fire_returns_retreat_result(
        self,
        _mock_random,
    ):
        mover = self._add_unit("mover", self.faction1, self.player1, 0, 1)
        defender = self._add_unit(
            "defender", self.faction2, self.player2, 1, 2
        )
        defender.record_friendly_turn_end(defender.get_move(), self.player1)

        results = self.resolver.resolve_defensive_fire(
            mover,
            self.board.get_hex(0, 1),
            self.player1,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].outcome, "retreat")
        self.assertEqual(results[0].retreat_destination, (0, 0))
        self.assertFalse(defender.has_defensive_fire(self.player1))

    @patch(
        RANDOM_PATCH_TARGET,
        side_effect=[1.0, 0.0],
    )
    def test_resolve_defensive_fire_uses_deterministic_defender_order(
        self,
        _mock_random,
    ):
        mover = self._add_unit("mover", self.faction1, self.player1, 0, 1)
        defender_b = self._add_unit(
            "b", self.faction2, self.player2, 1, 2
        )
        defender_a = self._add_unit(
            "a", self.faction2, self.player2, 0, 2
        )
        defender_a.record_friendly_turn_end(
            defender_a.get_move(),
            self.player1,
        )
        defender_b.record_friendly_turn_end(
            defender_b.get_move(),
            self.player1,
        )

        results = self.resolver.resolve_defensive_fire(
            mover,
            self.board.get_hex(0, 1),
            self.player1,
        )

        self.assertEqual(
            [result.firing_unit_id for result in results],
            ["a", "b"],
        )
        self.assertEqual(mover.get_coords(), (0, 0))

    def test_defensive_fire_probability_clamps_unit_and_terrain_modifiers(
        self,
    ):
        self.resolver.set_settings(
            DefensiveFireSettings(
                base_probability=0.5,
                minimum=0.1,
                maximum=0.3,
            )
        )
        defender = self._add_unit(
            "defender", self.faction2, self.player2, 1, 2
        )
        defender.defensive_fire_modifier = 2.0
        target_hex = self.board.get_hex(0, 1)
        target_hex.set_terrain(
            type(
                "Terrain",
                (),
                {"defensive_fire_modifier": 10.0, "move_cost": 1},
            )()
        )

        probability = self.resolver.defensive_fire_probability(
            defender,
            target_hex,
        )

        self.assertEqual(probability, 0.3)
