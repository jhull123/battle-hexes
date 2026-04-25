import uuid
from typing import List

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
from battle_hexes_core.unit.faction import Faction


class Game:
    def __init__(
        self,
        players: list,
        board: Board,
        turn_limit: int | None = None,
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
        self.defensive_fire_resolver = DefensiveFireResolver(board)
        self._refresh_defensive_fire_availability()

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

    def set_defensive_fire_settings(self, settings) -> None:
        self.defensive_fire_resolver.set_settings(settings)

    def apply_movement_plans(
        self,
        plans: List["UnitMovementPlan"],
    ) -> MovementResolutionResult:
        """Apply movement plans incrementally and resolve defensive fire."""
        movement = MovementCalculator(self.get_board())
        resolution = MovementResolutionResult()
        for plan in plans:
            if not plan.path:
                continue
            self._apply_single_movement_plan(plan, movement, resolution)
        self._refresh_defensive_fire_availability()
        self.get_current_player().movement_cb()
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
        self._reset_defensive_fire_off_turn_usage(self.current_player)
        self._refresh_defensive_fire_availability()
        return self.current_player

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
        if self.turn_limit is not None and self.turn_number > self.turn_limit:
            return True

        active_players = {
            unit.player.name
            for unit in self.get_board().get_units()
            if unit.get_coords() is not None
        }
        return len(active_players) <= 1
