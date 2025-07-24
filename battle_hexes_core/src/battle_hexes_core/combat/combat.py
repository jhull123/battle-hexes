from battle_hexes_core.game.game import Game
from battle_hexes_core.combat.combatresult import (
    CombatResult,
    CombatResultData,
)
from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.combat.combatsolver import CombatSolver


class Combat:
    def __init__(self, game: Game):
        self.game = game
        self.board = game.get_board()
        self.attacking_player = game.get_current_player()
        self.combat_solver = CombatSolver()

    def resolve_combat(self):
        combat_results = CombatResults()
        for battle_participants in self.find_combat():
            battle_result = self.__resolve_combat(battle_participants)
            combat_results.add_battle(battle_result)
        for player in self.game.get_players():
            player.combat_results(combat_results)
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
            case CombatResult.ATTACKER_RETREAT_2:
                battle_participants[0].forced_move(
                    battle_participants[1].get_coords(),
                    2
                )
                if not self.board.is_in_bounds(
                        battle_participants[0].row,
                        battle_participants[0].column):
                    self.board.remove_units(battle_participants[0])
            case CombatResult.DEFENDER_ELIMINATED:
                self.board.remove_units(battle_participants[1])
            case CombatResult.DEFENDER_RETREAT_2:
                battle_participants[1].forced_move(
                    battle_participants[0].get_coords(),
                    2
                )
                if not self.board.is_in_bounds(
                        battle_participants[1].row,
                        battle_participants[1].column):
                    self.board.remove_units(battle_participants[1])
            case CombatResult.EXCHANGE:
                self.board.remove_units(battle_participants)
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
