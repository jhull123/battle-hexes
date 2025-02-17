from src.game.game import Game
from src.combat.combatresult import CombatResult, CombatResultData
from src.combat.combatresults import CombatResults


class Combat:
    def __init__(self, game: Game):
        self.board = game.get_board()
        self.attacking_player = game.get_current_player()

    def resolve_combat(self):
        combat_results = CombatResults()
        for battle_participants in self.find_combat():
            print('battle participants:', battle_participants)
            fake_result = CombatResultData(
                (1, 1),
                1,
                CombatResult.ATTACKER_ELIMINATED
            )
            combat_results.add_battle(fake_result)
        return combat_results

    def find_combat(self) -> list:
        results = list()

        for unit in self.board.get_units():
            for other_unit in self.board.get_units():
                if not self.attacking_player.has_faction(unit.get_faction()):
                    # the unit is not an attacker
                    continue
                if self.attacking_player.has_faction(other_unit.get_faction()):
                    # the other unit is not an opponent
                    continue
                if unit.is_adjacent(other_unit):
                    results.append((unit, other_unit))

        return results
