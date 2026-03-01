import heapq
from itertools import count
from typing import TYPE_CHECKING, List, Set

from battle_hexes_core.game.hex import Hex
from battle_hexes_core.unit.unit import Unit

if TYPE_CHECKING:
    from battle_hexes_core.game.board import Board


class MovementCalculator:
    def __init__(self, board: "Board"):
        self.board = board

    def move_cost(self, unit: Unit, from_hex: Hex, to_hex: Hex) -> int:
        """Return movement cost for entering ``to_hex`` from ``from_hex``."""
        del unit, from_hex
        if to_hex.terrain is None:
            return 1
        return to_hex.terrain.move_cost

    def get_reachable_hexes(
            self, unit: Unit, start: Hex, move_points: int = None
    ) -> Set[Hex]:
        """Get all hexes reachable by the unit from the start hex."""
        if move_points is None:
            move_points = unit.get_move()

        min_cost_by_coord: dict[tuple[int, int], float] = {
            (start.row, start.column): 0,
        }
        reachable_hexes = {start}
        queue_counter = count()
        queue: list[tuple[float, int, Hex]] = [(0, next(queue_counter), start)]

        while queue:
            current_cost, _, current_hex = heapq.heappop(queue)
            current_coord = (current_hex.row, current_hex.column)
            if current_cost > min_cost_by_coord[current_coord]:
                continue

            if current_cost >= move_points:
                continue

            if self.board.enemy_adjacent(unit, current_hex):
                # Movement must stop when entering a hex adjacent to an enemy
                # unit, so do not expand further from this hex.
                continue

            for neighbor in self.board.get_neighboring_hexes(current_hex):
                step_cost = self.move_cost(unit, current_hex, neighbor)
                new_cost = current_cost + step_cost
                if new_cost > move_points:
                    continue

                coord = (neighbor.row, neighbor.column)
                prior_cost = min_cost_by_coord.get(coord, float("inf"))
                if new_cost < prior_cost:
                    min_cost_by_coord[coord] = new_cost
                    reachable_hexes.add(neighbor)
                    heapq.heappush(
                        queue,
                        (new_cost, next(queue_counter), neighbor),
                    )

        return reachable_hexes

    def shortest_path(
            self, unit: Unit, start: Hex, end: Hex
    ) -> List[Hex]:
        """Find the shortest path from start to end hex for the unit."""
        move_points = unit.get_move()
        reachable_hexes = self.get_reachable_hexes(unit, start, move_points)

        if end not in reachable_hexes:
            return []

        min_cost_by_coord: dict[tuple[int, int], float] = {
            (start.row, start.column): 0,
        }
        predecessor_by_coord: dict[tuple[int, int], tuple[int, int] | None] = {
            (start.row, start.column): None,
        }
        hex_by_coord: dict[tuple[int, int], Hex] = {
            (start.row, start.column): start,
        }
        queue_counter = count()
        queue: list[tuple[float, int, Hex]] = [(0, next(queue_counter), start)]

        while queue:
            current_cost, _, current_hex = heapq.heappop(queue)
            current_coord = (current_hex.row, current_hex.column)
            if current_cost > min_cost_by_coord[current_coord]:
                continue

            if current_hex == end:
                return self._build_path(
                    end,
                    predecessor_by_coord,
                    hex_by_coord,
                )

            if self.board.enemy_adjacent(unit, current_hex):
                # Cannot continue moving once adjacent to an enemy unit
                continue

            for neighbor in self.board.get_neighboring_hexes(current_hex):
                if neighbor not in reachable_hexes:
                    continue

                step_cost = self.move_cost(unit, current_hex, neighbor)
                new_cost = current_cost + step_cost
                if new_cost > move_points:
                    continue

                coord = (neighbor.row, neighbor.column)
                prior_cost = min_cost_by_coord.get(coord, float("inf"))
                if new_cost < prior_cost:
                    min_cost_by_coord[coord] = new_cost
                    predecessor_by_coord[coord] = current_coord
                    hex_by_coord[coord] = neighbor
                    heapq.heappush(
                        queue,
                        (new_cost, next(queue_counter), neighbor),
                    )

        return []

    def _build_path(
            self,
            end: Hex,
            predecessor_by_coord: dict[
                tuple[int, int],
                tuple[int, int] | None,
            ],
            hex_by_coord: dict[tuple[int, int], Hex],
    ) -> List[Hex]:
        coord = (end.row, end.column)
        path: list[Hex] = []
        while coord is not None:
            path.append(hex_by_coord[coord])
            coord = predecessor_by_coord[coord]

        path.reverse()
        return path
