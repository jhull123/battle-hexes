import uuid
from dataclasses import dataclass
from typing import List, Any

from battle_hexes_core.game.board import Board
from battle_hexes_core.defensivefire.defensive_fire import (
    MovementResolutionResult,
)
from battle_hexes_core.defensivefire.defensive_fire_resolver import (
    DefensiveFireResolver,
)
from battle_hexes_core.game.movement import MovementCalculator
from battle_hexes_core.game.player import Player
from battle_hexes_core.game.scoretracker import ScoreTracker
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.game.reinforcement import ReinforcementGroup
from battle_hexes_core.game.reinforcements_deployer import (
    ReinforcementsDeployer,
)
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.combat.combatsolver import CombatSolver


@dataclass
class EndTurnResult:
    previous_player: Player | None
    current_player: Player | None
    game_status: Any


class Game:
    def __init__(
        self,
        players: list,
        board: Board,
        turn_limit: int | None = None,
        reinforcements: list[ReinforcementGroup] | None = None,
    ):
        self.id = uuid.uuid4()
        self.players = players
        if players:
            self.current_player = players[0]
        self.board = board
        self.score_tracker = ScoreTracker(players)
        self.turn_limit = (
            turn_limit
            if isinstance(turn_limit, int) and turn_limit > 0
            else None
        )
        self.turn_number = 1
        self.reinforcements_deployer = ReinforcementsDeployer(
            board,
            reinforcements,
        )
        self.combat_log = []
        self.current_phase = "movement"
        self.pending_combats = []
        self.defensive_fire_resolver = DefensiveFireResolver(board)
        self._refresh_defensive_fire_availability()
        self.game_status = None
        self.combat_results_table = CombatSolver.get_combat_results_table()
        self._terminal = False
        self.reinforcements_deployer.deploy_due(self.turn_number)
        self.update_game_status()

    def get_id(self):
        return self.id

    def get_players(self):
        return self.players

    def get_board(self):
        return self.board

    def get_current_player(self) -> Player:
        return self.current_player

    def get_score_tracker(self) -> ScoreTracker:
        return self.score_tracker

    def get_combat_results_table(self):
        """Return the immutable reference used by combat resolution."""
        return self.combat_results_table

    def set_defensive_fire_settings(self, settings) -> None:
        self.defensive_fire_resolver.set_settings(settings)

    def apply_movement_plans(
        self,
        plans: List["UnitMovementPlan"],
    ) -> MovementResolutionResult:
        """Apply movement plans incrementally and resolve defensive fire."""
        self._require_in_progress()
        movement = MovementCalculator(self.get_board())
        resolution = MovementResolutionResult()
        for plan in plans:
            if not plan.path:
                continue
            self._apply_single_movement_plan(plan, movement, resolution)
        self._refresh_defensive_fire_availability()
        self.get_current_player().movement_cb()
        resolution.game_status = self.update_game_status(finalize=True)
        return resolution

    def _apply_single_movement_plan(
        self,
        plan: UnitMovementPlan,
        movement: MovementCalculator,
        resolution: MovementResolutionResult,
    ) -> None:
        unit = plan.unit
        if unit.get_coords() is None:
            return

        movement_points_remaining = (
            unit.current_turn_movement_points_remaining
        )
        for from_hex, to_hex in zip(plan.path, plan.path[1:]):
            if unit.get_coords() != (from_hex.row, from_hex.column):
                break

            if not self.board.can_unit_enter_hex(
                unit,
                to_hex.row,
                to_hex.column,
            ):
                break

            was_adjacent = self.board.enemy_adjacent(unit, from_hex)
            move_cost = movement.move_cost(unit, from_hex, to_hex)
            movement_points_remaining = max(
                movement_points_remaining - move_cost,
                0,
            )
            unit.set_coords(to_hex.row, to_hex.column)
            unit.current_turn_movement_points_remaining = (
                movement_points_remaining
            )

            if was_adjacent:
                continue

            if not self.board.enemy_adjacent(unit, to_hex):
                continue

            unit.current_turn_movement_points_remaining = 0
            defensive_fire_results = (
                self.defensive_fire_resolver.resolve_defensive_fire(
                    unit,
                    to_hex,
                    self.get_current_player(),
                )
            )
            resolution.defensive_fire_results.extend(defensive_fire_results)
            break

    def next_player(self) -> Player:
        """Advance to the next player and return it."""
        if not self.players:
            return None

        previous_player = self.current_player
        self._snapshot_defensive_fire_eligibility(previous_player)

        idx = self.players.index(self.current_player)
        next_idx = (idx + 1) % len(self.players)
        if next_idx == 0:
            self.turn_number += 1
        self.current_player = self.players[next_idx]
        if next_idx == 0:
            self.reinforcements_deployer.deploy_due(self.turn_number)
        self._reset_movement_for_new_turn(self.current_player)
        self._reset_defensive_fire_off_turn_usage(self.current_player)
        self._refresh_defensive_fire_availability()
        self.update_game_status(finalize=True)
        return self.current_player

    def _reset_movement_for_new_turn(self, player: Player) -> None:
        for unit in self.get_board().get_units_for_player(player):
            unit.current_turn_movement_points_remaining = unit.get_move()

    def end_turn(self) -> EndTurnResult:
        """Advance the turn and return the resulting core state."""
        self._require_in_progress()
        previous_player = self.get_current_player() if self.players else None
        self.update_game_status(turn_ended=True, finalize=True)
        if self.is_game_over():
            self._terminal = True
            self.current_player = None
            self.current_phase = None
            self.pending_combats = []
            return EndTurnResult(
                previous_player=previous_player,
                current_player=None,
                game_status=self.get_game_status(),
            )
        current_player = self.next_player()
        self.current_phase = "movement"
        self.pending_combats = []
        return EndTurnResult(
            previous_player=previous_player,
            current_player=current_player,
            game_status=self.get_game_status(),
        )

    def end_movement(self) -> None:
        """Finish movement and persist the combats that must be resolved."""
        self._require_in_progress()
        from battle_hexes_core.combat.combat import Combat

        self.pending_combats = [
            {
                "attacker_unit_ids": [
                    str(unit.get_id()) for unit in attackers
                ],
                "defender_unit_ids": [
                    str(unit.get_id()) for unit in defenders
                ],
            }
            for attackers, defenders in Combat(self).find_combat()
        ]
        self.current_phase = (
            "combat" if self.pending_combats else "end_turn"
        )

    def end_combat(self) -> None:
        """Record that all pending combat has been resolved."""
        self._require_in_progress()
        self.pending_combats = []
        self.current_phase = "end_turn"

    def update_game_status(
        self,
        *,
        turn_ended: bool = False,
        finalize: bool = False,
    ):
        """Evaluate and store the current core game status."""
        from battle_hexes_core.scoring.game_status_evaluator import (
            GameStatusEvaluator,
        )

        previous_state = getattr(self.game_status, "state", None)
        self.game_status = GameStatusEvaluator().evaluate(
            self,
            turn_ended=turn_ended,
        )
        if (
            finalize
            and previous_state == "in_progress"
            and self.game_status.state == "completed"
        ):
            self._terminal = True
        return self.game_status

    def get_game_status(self):
        """Return the latest core game status for this game."""
        if self.game_status is None:
            return self.update_game_status()
        return self.game_status

    def _snapshot_defensive_fire_eligibility(
            self,
            player: Player,
    ) -> None:
        for unit in self.get_board().get_units_for_player(player):
            unit.record_friendly_turn_end(
                unit.current_turn_movement_points_remaining,
                self.current_player,
            )

    def _reset_defensive_fire_off_turn_usage(self, player: Player) -> None:
        for unit in self.get_board().get_units_for_player(player):
            unit.reset_defensive_fire_for_new_turn(self.current_player)

    def _refresh_defensive_fire_availability(self) -> None:
        for unit in self.get_board().get_units():
            unit.update_defensive_fire_available(self.current_player)

    def get_opposing_factions(self, faction: Faction) -> List[Faction]:
        owning_player = self.get_player_for_faction(faction)
        opposing_factions = []
        for player in self.players:
            if player != owning_player:
                opposing_factions.extend(player.factions)
        return opposing_factions

    def get_player_for_faction(self, faction: Faction) -> Player:
        for player in self.players:
            if faction in player.factions:
                return player
        raise ValueError(f"No player found for faction {faction.name}")

    def get_turn_limit(self) -> int | None:
        return self.turn_limit

    def get_turn_number(self) -> int:
        return self.turn_number

    def is_game_over(self) -> bool:
        """Return True if zero/one players remain or turn limit was reached."""
        if self._terminal:
            return True
        if self.turn_limit is not None and self.turn_number > self.turn_limit:
            return True

        active_players = {
            unit.player.name
            for unit in self.get_board().get_units()
            if unit.get_coords() is not None
        }
        active_players.update(
            player.name
            for player in self.players
            if self.reinforcements_deployer.has_eligible_pending(
                player,
                self.turn_number,
                self.turn_limit,
            )
        )
        return len(active_players) <= 1

    def _require_in_progress(self) -> None:
        """Reject mutations after the game reaches a terminal state."""
        if self._terminal:
            raise RuntimeError("Game is already completed")
