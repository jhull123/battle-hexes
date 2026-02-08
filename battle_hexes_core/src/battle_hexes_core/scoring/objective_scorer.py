import logging

from battle_hexes_core.combat.combat import Combat
from battle_hexes_core.combat.combatresult import CombatResult
from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.game import Game

logger = logging.getLogger(__name__)


class ObjectiveScorer:
    """Award points for objectives held at the end of movement."""

    def award_hold_objectives(self, game: Game) -> int:
        """Award points to the current player for held objectives."""
        current_player = game.get_current_player()
        score_tracker = game.get_score_tracker()
        engaged_unit_ids = self._get_engaged_unit_ids(game, current_player)
        held_objectives = self._get_held_objectives(
            game, current_player, engaged_unit_ids
        )
        total_points = sum(objective.points for objective in held_objectives)

        if total_points:
            score_tracker.add_points(current_player, total_points)
            self._log_awarded_points(
                current_player.name, total_points, held_objectives
            )

        return total_points

    def award_hold_objectives_after_combat(
        self, game: Game, combat_results: CombatResults
    ) -> int:
        """Award points for surviving attackers on objectives."""
        current_player = game.get_current_player()
        score_tracker = game.get_score_tracker()
        eligible_attacker_ids = self._get_eligible_attacker_ids(
            combat_results, current_player
        )
        held_objectives = self._get_post_combat_held_objectives(
            game, eligible_attacker_ids
        )
        total_points = sum(objective.points for objective in held_objectives)
        if total_points:
            score_tracker.add_points(current_player, total_points)
            self._log_awarded_points(
                current_player.name, total_points, held_objectives
            )
        return total_points

    def _get_eligible_attacker_ids(
        self, combat_results: CombatResults, current_player
    ) -> set[str]:
        """Return attacker IDs that remain eligible after combat."""
        eligible_attacker_ids = set()
        for battle in combat_results.get_battles():
            participants = battle.get_battle_participants()
            if participants is None:
                continue
            if battle.get_combat_result() == CombatResult.ATTACKER_RETREAT_2:
                continue
            attackers, _ = participants
            for attacker in attackers:
                if current_player.owns(attacker):
                    eligible_attacker_ids.add(attacker.get_id())
        return eligible_attacker_ids

    def _get_post_combat_held_objectives(
        self, game: Game, eligible_attacker_ids: set[str]
    ) -> list:
        """Return hold objectives occupied by surviving attackers."""
        board = game.get_board()
        held_objectives = []
        for objective in board.get_objectives():
            if objective.type != "hold":
                continue
            row, column = objective.coords
            if any(
                unit.get_id() in eligible_attacker_ids
                and unit.get_coords() == (row, column)
                for unit in board.get_units()
            ):
                held_objectives.append(objective)
        return held_objectives

    def _get_engaged_unit_ids(self, game: Game, current_player) -> set[str]:
        """Return IDs for the current player's units engaged in combat."""
        combat = Combat(game)
        return {
            unit.get_id()
            for attackers, defenders in combat.find_combat()
            for unit in attackers + defenders
            if current_player.owns(unit)
        }

    def _get_held_objectives(
        self, game: Game, current_player, engaged_unit_ids: set[str]
    ) -> list:
        """Return hold objectives occupied by eligible current-player units."""
        board = game.get_board()
        held_objectives = []
        for objective in board.get_objectives():
            if objective.type != "hold":
                continue
            if self._objective_is_held(
                board, objective, current_player, engaged_unit_ids
            ):
                held_objectives.append(objective)
        return held_objectives

    def _objective_is_held(
        self, board, objective, current_player, engaged_unit_ids: set[str]
    ) -> bool:
        """Return True when the objective is held by eligible units."""
        row, column = objective.coords
        return any(
            unit.get_coords() == (row, column)
            and current_player.owns(unit)
            and unit.get_id() not in engaged_unit_ids
            for unit in board.get_units()
        )

    def _log_awarded_points(
        self, player_name: str, total_points: int, held_objectives: list
    ) -> None:
        """Log awarded points for held objectives."""
        logger.info(
            "Awarded %s points to %s for holding objectives at %s.",
            total_points,
            player_name,
            [objective.coords for objective in held_objectives],
        )
