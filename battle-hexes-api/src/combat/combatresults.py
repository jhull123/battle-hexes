from typing import List
from src.combat.combatresult import CombatResult


class CombatResults:
    def __init__(self):
        self.battles: List[CombatResult] = []

    def add_battle(self, battle: CombatResult) -> None:
        self.battles.append(battle)

    def get_battles(self):
        return self.battles
