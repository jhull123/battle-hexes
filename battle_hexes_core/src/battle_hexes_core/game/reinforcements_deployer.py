"""Deploy scenario reinforcements and report their pending state."""

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player
from battle_hexes_core.game.reinforcement import ReinforcementGroup


class ReinforcementsDeployer:
    """Own reinforcement arrival behavior for a running game."""

    def __init__(
        self,
        board: Board,
        groups: list[ReinforcementGroup] | None = None,
    ) -> None:
        self.board = board
        self.groups = list(groups or [])

    def deploy_due(self, turn_number: int) -> None:
        """Place due fixed groups in declaration order when entry is legal."""
        for group in self.groups:
            if group.entered or group.arrival_turn > turn_number:
                continue
            if not self._can_deploy(group):
                continue
            row, column = group.coords
            for unit in group.units:
                self.board.add_unit(unit, row, column)
            group.entered = True

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
