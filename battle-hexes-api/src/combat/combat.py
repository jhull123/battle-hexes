from src.game.game import Game
from src.combat.combatresult import CombatResult, CombatResultData
from src.combat.combatresults import CombatResults
from src.combat.combatsolver import CombatSolver


class Combat:
    def __init__(self, game: Game):
        self.board = game.get_board()
        self.attacking_player = game.get_current_player()
        self.combat_solver = CombatSolver()

    def resolve_combat(self):
        combat_results = CombatResults()
        for battle_participants in self.find_combat():
            battle_result = self.__resolve_combat(battle_participants)
            combat_results.add_battle(battle_result)
        return combat_results

    def __resolve_combat(self, battle_participants) -> CombatResultData:
        attack_factor = battle_participants[0].get_attack()
        defense_factor = battle_participants[1].get_defense()
        combat_result = self.combat_solver.solve_combat(
            attack_factor,
            defense_factor
        )
        self.__update_board_for_result(battle_participants, combat_result)
        return combat_result

    def __update_board_for_result(
            self,
            battle_participants,
            combat_result: CombatResultData
    ) -> None:
        match combat_result.get_combat_result():
            case CombatResult.ATTACKER_ELIMINATED:
                self.board.remove_units(battle_participants[0])
            case _:
                raise Exception(
                    'Unhandled combat result:',
                    combat_result.get_combat_result()
                )

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

    def set_static_die_roll(self, static_die_roll: int) -> None:
        self.combat_solver.set_static_die_roll(static_die_roll)
