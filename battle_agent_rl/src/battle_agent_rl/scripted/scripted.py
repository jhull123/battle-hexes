"""Scripted CPU policy for ordinary core turns."""

from collections import Counter

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.hex import Hex
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .balanced_assignment import balanced_target_indices
from .movement_projection import MovementProjection

Coords = tuple[int, int]


class ScriptedPlayer(Player):
    """Advance each unit toward its assigned objective."""

    def __init__(
        self,
        name: str,
        factions: list[Faction] | None = None,
        board: Board | None = None,
    ) -> None:
        super().__init__(name, PlayerType.CPU, factions or [])
        self._board = board
        self._assignments: dict[str, Coords] = {}

    def game_started_cb(self, board: Board) -> None:
        self._board = board
        self.initialize_objective_assignments()

    def initialize_objective_assignments(self) -> None:
        """Balance assignments from the starting or restored legacy board."""
        objectives = self._objective_hexes()
        if not objectives:
            self._assignments = {}
            return

        targets = list(objectives)
        units = self._deployed_units()
        distances = [
            [Board.hex_distance(start, hex_) for hex_ in objectives.values()]
            for _, start in units
        ]
        self._assignments = {
            _unit_id(unit): targets[index]
            for (unit, _), index in zip(
                units, balanced_target_indices(distances), strict=True,
            )
        }

    def objective_assignments(self) -> dict[str, Coords]:
        """Return the targets of living, deployed units for persistence."""
        return {
            unit_id: self._assignments[unit_id]
            for unit, _ in self._deployed_units()
            if (unit_id := _unit_id(unit)) in self._assignments
        }

    def restore_objective_assignments(
        self, assignments: dict[str, Coords],
    ) -> None:
        self._assignments = assignments.copy()

    def reinforcements_arrived_cb(
        self, units: tuple[Unit, ...], coords: Coords,
    ) -> None:
        board = self._board
        if board is None or not (objectives := self._objective_hexes()):
            return
        entry = board.get_hex(*coords)
        assert entry is not None  # the group has been placed by core
        distances = {
            target: Board.hex_distance(entry, hex_)
            for target, hex_ in objectives.items()
        }
        counts = Counter(self.objective_assignments().values())
        for unit in sorted(units, key=_unit_id):
            unit_id = _unit_id(unit)
            if unit_id not in self._assignments:
                target = min(
                    objectives, key=lambda c: (counts[c], distances[c], c),
                )
                self._assignments[unit_id] = target
                counts[target] += 1

    def movement(self) -> list[UnitMovementPlan]:
        board = self._board
        if board is None or not (objectives := self._objective_hexes()):
            return []

        projection = MovementProjection(board)
        plans = []
        for unit, start in self._deployed_units():
            target_coords = self._assignments.get(_unit_id(unit))
            target = objectives.get(target_coords)
            if target is None:
                continue
            path = _path_toward_objective(
                projection.board, unit, start, target,
            )
            if path:
                plan = UnitMovementPlan(unit, path)
                projection.accept(plan)
                plans.append(plan)
        return plans

    def _deployed_units(self) -> list[tuple[Unit, Hex]]:
        board = self._board
        if board is None:
            return []
        return [
            (unit, start)
            for unit in sorted(board.get_units_for_player(self), key=_unit_id)
            if (coords := unit.get_coords()) is not None
            and (start := board.get_hex(*coords)) is not None
        ]

    def _objective_hexes(self) -> dict[Coords, Hex]:
        board = self._board
        if board is None:
            return {}
        coords_set = {obj.coords for obj in board.get_objectives()}
        return {
            coords: hex_
            for coords in sorted(coords_set)
            if (hex_ := board.get_hex(*coords)) is not None
        }

    def combat_results(self, combat_results: CombatResults) -> None:
        pass


def _unit_id(unit: Unit) -> str:
    return str(unit.get_id())


def _distance_key(origin: Hex, candidate: Hex) -> tuple[int, int, int]:
    return (
        Board.hex_distance(origin, candidate), candidate.row, candidate.column
    )


def _path_toward_objective(
    board: Board, unit: Unit, start: Hex, target: Hex,
) -> list[Hex]:
    if start == target:
        return []

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
