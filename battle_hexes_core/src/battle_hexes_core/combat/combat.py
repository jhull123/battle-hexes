from itertools import combinations

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

    def resolve_combat(self) -> CombatResults:
        combat_results = CombatResults()
        for attackers, defenders in self.find_combat():
            if not attackers or not defenders:
                continue
            if (
                any(a.get_coords() is None for a in attackers)
                or any(d.get_coords() is None for d in defenders)
            ):
                # A participant may have been removed earlier in the turn
                # (e.g. by another combat). Skip invalid groups.
                continue
            battle_result = self.__resolve_combat((attackers, defenders))
            combat_results.add_battle(battle_result)
        for player in self.game.get_players():
            player.combat_results(combat_results)
        return combat_results

    def __resolve_combat(self, battle_participants) -> CombatResultData:
        attackers, defenders = battle_participants
        attack_factor = sum(unit.get_attack() for unit in attackers)
        defense_factor = sum(unit.get_defense() for unit in defenders)
        combat_result = self.combat_solver.solve_combat(
            attack_factor,
            defense_factor
        )
        combat_result.set_battle_participants((attackers, defenders))
        self.__update_board_for_result((attackers, defenders), combat_result)
        return combat_result

    def __update_board_for_result(
            self,
            battle_participants,
            combat_result: CombatResultData
    ) -> None:
        attackers, defenders = battle_participants
        if (
            any(a.get_coords() is None for a in attackers)
            or any(d.get_coords() is None for d in defenders)
        ):
            # One or more units no longer occupy the board. Nothing to update.
            return
        match combat_result.get_combat_result():
            case CombatResult.ATTACKER_ELIMINATED:
                self.board.remove_units(attackers)
            case CombatResult.ATTACKER_RETREAT_2:
                origin = defenders[0].get_coords()
                removed = []
                for attacker in attackers:
                    success = attacker.forced_move(self.board, origin, 2)
                    if not success:
                        removed.append(attacker)
                if removed:
                    self.board.remove_units(removed)
                    combat_result.add_no_retreat_units(removed)
                    if len(removed) == len(attackers):
                        combat_result.combat_result = (
                            CombatResult.ATTACKER_ELIMINATED
                        )
            case CombatResult.DEFENDER_ELIMINATED:
                self.board.remove_units(defenders)
            case CombatResult.DEFENDER_RETREAT_2:
                origin = attackers[0].get_coords()
                removed = []
                for defender in defenders:
                    success = defender.forced_move(self.board, origin, 2)
                    if not success:
                        removed.append(defender)
                if removed:
                    self.board.remove_units(removed)
                    combat_result.add_no_retreat_units(removed)
                    if len(removed) == len(defenders):
                        combat_result.combat_result = (
                            CombatResult.DEFENDER_ELIMINATED
                        )
            case CombatResult.EXCHANGE:
                defense_factor = sum(
                    unit.get_defense() for unit in defenders
                )
                attackers_to_remove = self._attackers_to_remove(
                    attackers,
                    defense_factor,
                )
                self.board.remove_units(attackers_to_remove + defenders)
            case _:
                raise Exception(
                    'Unhandled combat result:',
                    combat_result.get_combat_result(),
                )

    def _attackers_to_remove(self, attackers, defense_factor):
        """Return subset of attackers to remove for an exchange."""
        best_subset = list(attackers)
        best_total = sum(u.get_attack() for u in attackers)
        for size in range(1, len(attackers) + 1):
            for combo in combinations(attackers, size):
                total = sum(u.get_attack() for u in combo)
                if total >= defense_factor:
                    if (
                        len(combo) < len(best_subset)
                        or (
                            len(combo) == len(best_subset)
                            and total < best_total
                        )
                    ):
                        best_subset = list(combo)
                        best_total = total
            if len(best_subset) == size:
                break
        return best_subset

    def find_combat(self) -> list:
        results = []
        units = self.board.get_units()
        engaged_units = [
            u for u in units
            if any(
                (
                    u.get_coords() == other.get_coords()
                    or u.is_adjacent(other)
                ) and not u.is_friendly(other)
                for other in units
            )
        ]
        visited: set[object] = set()

        for unit in engaged_units:
            if unit in visited:
                continue

            stack = [unit]
            component = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                for other in engaged_units:
                    if other in visited:
                        continue
                    if (
                        current.get_coords() == other.get_coords()
                        or current.is_adjacent(other)
                    ):
                        stack.append(other)

            attackers = [
                u for u in component
                if self.attacking_player.has_faction(u.get_faction())
            ]
            defenders = [
                u for u in component
                if not self.attacking_player.has_faction(u.get_faction())
            ]
            if attackers and defenders:
                results.append((attackers, defenders))

        return results

    def set_static_die_roll(self, static_die_roll: int) -> None:
        self.combat_solver.set_static_die_roll(static_die_roll)
