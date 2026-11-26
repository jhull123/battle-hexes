"""Scripted CPU policy for ordinary core turns."""

from collections import Counter
from collections.abc import Callable

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.hex import Hex
from battle_hexes_core.game.movement import MovementCalculator
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .balanced_assignment import balanced_target_indices, exact_target_indices
from .movement_projection import MovementProjection
from .opening import OpeningSampler

Coords = tuple[int, int]
ReinforcementAssignmentObserver = Callable[
    [Coords, dict[str, Coords]], None
]


class ScriptedPlayer(Player):
    """Advance each unit toward its assigned objective."""

    def __init__(
        self,
        name: str,
        factions: list[Faction] | None = None,
        board: Board | None = None,
        *,
        opening_sampler: OpeningSampler | None = None,
    ) -> None:
        super().__init__(name, PlayerType.CPU, factions or [])
        self._board = board
        self._opening_sampler = opening_sampler
        self._assignments: dict[str, Coords] = {}
        self.on_reinforcement_assignments: (
            ReinforcementAssignmentObserver | None
        ) = None

    def game_started_cb(self, board: Board) -> None:
        self._board = board
        self._initialize_assignments(self._opening_sampler)

    def initialize_objective_assignments(self) -> None:
        """Balance assignments deterministically on a restored legacy board."""
        self._initialize_assignments(None)

    def _initialize_assignments(self, sample: OpeningSampler | None) -> None:
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
        if sample is None:
            indices = balanced_target_indices(distances)
        else:
            indices = exact_target_indices(
                distances, sample(len(units), len(objectives)),
            )
        self._assignments = {
            _unit_id(unit): targets[index]
            for (unit, _), index in zip(units, indices, strict=True)
        }

    def objective_assignments(self) -> dict[str, Coords]:
        """Return the targets of living, deployed units for persistence."""
        return {
            unit_id: self._assignments[unit_id]
            for unit, _ in self._deployed_units()
            if (unit_id := _unit_id(unit)) in self._assignments
        }

    def objective_assignment_counts(self) -> dict[Coords, int]:
        """Count living assignments in objective order, including zeros."""
        counts = Counter(self.objective_assignments().values())
        return {target: counts[target] for target in self._objective_hexes()}

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
        assigned = {}
        for unit in sorted(units, key=_unit_id):
            unit_id = _unit_id(unit)
            if unit_id not in self._assignments:
                target = min(
                    objectives, key=lambda c: (counts[c], distances[c], c),
                )
                self._assignments[unit_id] = target
                assigned[unit_id] = target
                counts[target] += 1

        if assigned and self.on_reinforcement_assignments is not None:
            self.on_reinforcement_assignments(coords, assigned)

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


def _path_toward_objective(
    board: Board, unit: Unit, start: Hex, target: Hex,
) -> list[Hex]:
    if start == target:
        return []

    movement = MovementCalculator(board)
    costs = movement.get_reachable_hex_costs(
        unit, start, unit.current_turn_movement_points_remaining,
    )
    destination = min(costs, key=lambda hex_: (
        Board.hex_distance(target, hex_), costs[hex_], hex_.row, hex_.column,
    ))
    # A reachable target wins at distance zero. When it is blocked, distance
    # one prefers a neighbor; strict progress prevents shuffling among them.
    if (
        Board.hex_distance(target, destination)
        >= Board.hex_distance(target, start)
    ):
        return []

    # This is a least-cost path on the same occupancy. Reachability above
    # already proves its cost fits the remaining (at most full) allowance.
    return movement.shortest_path(unit, start, destination)
