"""Deploy scenario reinforcements and report their pending state."""

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player
from battle_hexes_core.game.reinforcement import (
    PendingReinforcementGroup,
    ReinforcementArrivalEvent,
    ReinforcementGroup,
)


class ReinforcementsDeployer:
    """Own reinforcement arrival behavior for a running game."""

    def __init__(
        self,
        board: Board,
        groups: list[ReinforcementGroup] | None = None,
    ) -> None:
        self.board = board
        self.groups = list(groups or [])
        self.game_log: list[ReinforcementArrivalEvent] = []

    def deploy_due(self, turn_number: int) -> None:
        """Place due fixed groups in declaration order when entry is legal."""
        for group in self.groups:
            if group.entered or group.arrival_turn > turn_number:
                continue
            can_deploy = self._can_deploy(group)
            if not can_deploy:
                self._record_attempt(group, turn_number, "blocked")
                continue
            row, column = group.coords
            for unit in group.units:
                self.board.add_unit(unit, row, column)
            group.entered = True
            self._record_attempt(group, turn_number, "arrived")

    def _record_attempt(self, group, turn_number, outcome) -> None:
        self.game_log.append(ReinforcementArrivalEvent(
            turn_number=turn_number,
            player_name=group.player.name,
            unit_count=len(group.units),
            entry_coordinate=group.coords,
            outcome=outcome,
        ))

    def has_eligible_pending(
        self,
        player: Player,
        turn_number: int,
        turn_limit: int | None,
    ) -> bool:
        """Return whether a player's pending group has time left to enter."""
        for group in self.groups:
            if group.entered or group.player is not player:
                continue
            if turn_limit is None:
                return True
            next_attempt = max(group.arrival_turn, turn_number + 1)
            if next_attempt <= turn_limit:
                return True
        return False

    def pending(
        self,
        turn_number: int,
    ) -> tuple[PendingReinforcementGroup, ...]:
        """Return authoritative pending state in scenario declaration order."""
        return tuple(
            PendingReinforcementGroup(
                units=group.units,
                arrival_turn=group.arrival_turn,
                coords=group.coords,
                status=(
                    "delayed"
                    if group.arrival_turn < turn_number
                    else "scheduled"
                ),
            )
            for group in self.groups
            if not group.entered
        )

    def _can_deploy(self, group: ReinforcementGroup) -> bool:
        row, column = group.coords
        if not self.board.is_in_bounds(row, column):
            return False
        occupants = self.board.get_units_at(row, column)
        if any(
            not occupant.is_friendly(group.units[0])
            for occupant in occupants
        ):
            return False
        limit = self.board.stacking_limit
        return limit is None or len(occupants) + len(group.units) <= limit
