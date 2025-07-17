import unittest
import uuid
from battle_hexes_core.unit.unit import Unit
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction


class TestUnit(unittest.TestCase):
    def setUp(self):
        self.faction1 = Faction(id=uuid.uuid4(), name="Faction1", color="Red")
        self.faction2 = Faction(id=uuid.uuid4(), name="Faction2", color="Blue")
        self.player1 = Player(
            name="Player1",
            type=PlayerType.CPU,
            factions=[self.faction1]
        )
        self.player2 = Player(
            name="Player2",
            type=PlayerType.CPU,
            factions=[self.faction2]
        )

        self.unit1 = Unit(
            id=uuid.uuid4(),
            name="Unit1",
            player=self.player1,
            faction=self.faction1,
            type="Infantry",
            attack=10,
            defense=5,
            move=3,
            row=0,
            column=0
        )

        self.unit2 = Unit(
            id=uuid.uuid4(),
            name="Unit2",
            player=self.player1,
            faction=self.faction1,
            type="Cavalry",
            attack=12,
            defense=6,
            move=4,
            row=1,
            column=1
        )

        self.unit3 = Unit(
            id=uuid.uuid4(),
            name="Unit3",
            player=self.player2,
            faction=self.faction2,
            type="Archer",
            attack=8,
            defense=4,
            move=2,
            row=2,
            column=2
        )

    def test_is_friendly_same_player(self):
        self.assertTrue(self.unit1.is_friendly(self.unit2))

    def test_is_friendly_different_player(self):
        self.assertFalse(self.unit1.is_friendly(self.unit3))
