"""Stateless scripted CPU policy for ordinary core turns."""

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.hex import Hex
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .movement_projection import MovementProjection


class ScriptedPlayer(Player):
    """Advance each unit toward its nearest objective this turn."""

    def __init__(
        self,
        name: str,
        factions: list[Faction] | None = None,
        board: Board | None = None,
    ) -> None:
        super().__init__(name, PlayerType.CPU, factions or [])
        self._board = board

    def movement(self) -> list[UnitMovementPlan]:
        board = self._board
        if board is None:
            return []

        objectives = {
            hex_
            for objective in board.get_objectives()
            if (hex_ := board.get_hex(*objective.coords)) is not None
        }
        if not objectives:
            return []

        projection = MovementProjection(board)
        units = sorted(
            board.get_units_for_player(self),
            key=lambda unit: str(unit.get_id()),
        )
        plans = []
        for unit in units:
            path = _path_toward_objective(projection.board, unit, objectives)
            if path:
                plan = UnitMovementPlan(unit, path)
                projection.accept(plan)
                plans.append(plan)
        return plans

    def combat_results(self, combat_results: CombatResults) -> None:
        pass


def _distance_key(origin: Hex, candidate: Hex) -> tuple[int, int, int]:
    return (
        Board.hex_distance(origin, candidate), candidate.row, candidate.column
    )


def _path_toward_objective(
    board: Board, unit: Unit, objectives: set[Hex],
) -> list[Hex]:
    coords = unit.get_coords()
    if coords is None:
        return []
    start = board.get_hex(*coords)
    if start is None or start in objectives:
        return []

    target = min(objectives, key=lambda hex_: _distance_key(start, hex_))
    reachable = board.get_reachable_hexes(
        unit, start, unit.current_turn_movement_points_remaining,
    )
    destination = min(reachable, key=lambda hex_: _distance_key(target, hex_))
    # A reachable target wins at distance zero. When it is blocked, distance
    # one prefers a neighbor; strict progress prevents shuffling among them.
    if (
        Board.hex_distance(target, destination)
        >= Board.hex_distance(target, start)
    ):
        return []

    # This is a least-cost path on the same occupancy. Reachability above
    # already proves its cost fits the remaining (at most full) allowance.
    return board.shortest_path(unit, start, destination)
