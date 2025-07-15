from typing import List
from battle_hexes_core.combat.combatresult import CombatResult


class CombatResults:
    def __init__(self):
        self.battles: List[CombatResult] = []

    def add_battle(self, battle: CombatResult) -> None:
        self.battles.append(battle)

    def get_battles(self):
        return self.battles

    def battles_as_result_schema(self):
        return [battle.to_schema() for battle in self.battles]

    def __str__(self):
        s = f'{len(self.battles)} Battles\n'
        for battle in self.battles:
            s += f'Result: {battle.get_combat_result()}, '
            s += f'Odds: {battle.get_odds()[0]}:{battle.get_odds()[1]}, '
            s += f'Roll: {battle.get_die_roll()}'
        return s
