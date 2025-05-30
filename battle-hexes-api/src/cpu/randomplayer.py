from src.game.player import Player, PlayerType
from src.unit.faction import Faction
from typing import List


class RandomPlayer(Player):
    def __init__(self, name: str, type: PlayerType, factions: List[Faction]):
        super().__init__(name=name, type=type, factions=factions)
