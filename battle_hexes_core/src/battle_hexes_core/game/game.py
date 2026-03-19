import uuid
from typing import List

from battle_hexes_core.game.board import Board
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

    def apply_movement_plans(self, plans: List["UnitMovementPlan"]) -> None:
        """Apply a collection of movement plans to update unit positions."""
        movement = MovementCalculator(self.get_board())
        for plan in plans:
            if not plan.path:
                continue

            movement_points_spent = 0
            for from_hex, to_hex in zip(plan.path, plan.path[1:]):
                movement_points_spent += movement.move_cost(
                    plan.unit,
                    from_hex,
                    to_hex,
                )

            final_hex = plan.path[-1]
            plan.unit.set_coords(final_hex.row, final_hex.column)
            if (
                plan.unit.get_move() > 0
                and (
                    movement_points_spent >= plan.unit.get_move() - 1
                    or self.get_board().enemy_adjacent(plan.unit, final_hex)
                )
            ):
                plan.unit.set_defensive_fire_available(False)
        self.get_current_player().movement_cb()

    def next_player(self) -> Player:
        """Advance to the next player and return it."""
        if not self.players:
            return None
        idx = self.players.index(self.current_player)
        next_idx = (idx + 1) % len(self.players)
        if next_idx == 0:
            self.turn_number += 1
        self.current_player = self.players[next_idx]
        for unit in self.get_board().get_units():
            if self.current_player.owns(unit):
                unit.set_defensive_fire_available(True)
        return self.current_player

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
