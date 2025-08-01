from collections.abc import Iterable
from collections import deque
from pydantic import BaseModel
from typing import List, Set
from uuid import UUID
from battle_hexes_core.game.hex import Hex
from battle_hexes_core.game.sparseboard import SparseBoard
from battle_hexes_core.unit.unit import Unit, UnitModel


class BoardModel(BaseModel):
    rows: int
    columns: int
    units: List[UnitModel]


class Board:
    # Directions for even-numbered rows (0, 2, 4, ...)
    EVEN_R_DIRECTIONS = [
        (-1, 0),   # North
        (-1, +1),  # Northeast
        (0, +1),   # Southeast
        (+1, 0),   # South
        (0, -1),   # Southwest
        (-1, -1),  # Northwest
    ]

    # Directions for odd-numbered rows (1, 3, 5, ...)
    ODD_R_DIRECTIONS = [
        (-1, 0),   # North
        (0, +1),   # Northeast
        (+1, +1),  # Southeast
        (+1, 0),   # South
        (+1, -1),  # Southwest
        (0, -1),   # Northwest
    ]

    def __init__(self, rows: int, columns: int):
        self.rows = rows
        self.columns = columns
        self.units: dict[UUID, Unit] = {}
        self.hexes = []
        for row in range(rows):
            for column in range(columns):
                self.hexes.append(Hex(row, column))

    def get_rows(self) -> int:
        return self.rows

    def get_columns(self) -> int:
        return self.columns

    def get_hex(self, row: int, column: int) -> Hex | None:
        if 0 <= row < self.rows and 0 <= column < self.columns:
            index = row * self.columns + column
            return self.hexes[index]
        return None

    def is_in_bounds(self, row: int, column: int) -> bool:
        """Return True if the coordinates are on the board."""
        return 0 <= row < self.rows and 0 <= column < self.columns

    def add_unit(self, unit: Unit, row: int, column: int) -> None:
        if not (0 <= row < self.rows) or not (0 <= column < self.columns):
            raise ValueError("Unit is out of bounds")

        unit.set_coords(row, column)
        self.units[unit.get_id()] = unit

    def remove_units(self, units) -> None:
        if isinstance(units, Iterable):
            for unit in units:
                self._remove_single_unit(unit)
        else:
            self._remove_single_unit(units)

    def _remove_single_unit(self, unit: Unit):
        del self.units[unit.get_id()]
        unit.set_coords(None, None)

    def get_units(self) -> List[Unit]:
        return list(self.units.values())

    def get_unit_by_id(self, unit_id: UUID) -> Unit:
        if not isinstance(unit_id, UUID):
            unit_id = UUID(unit_id)
        unit = self.units.get(unit_id)
        if not unit:
            raise KeyError(f"No unit found with ID {unit_id}")
        return unit

    def update(self, sparse_board: SparseBoard) -> None:
        for unit_data in sparse_board.units:
            unit_id = unit_data.id
            if isinstance(unit_id, str):
                unit_id = UUID(unit_id)
            unit = self.get_unit_by_id(unit_id)
            unit.set_coords(unit_data.row, unit_data.column)

    def find_units(self, factions) -> List[Unit]:
        if isinstance(factions, Iterable):
            return [
                unit for unit in self.get_units()
                if unit.get_faction() in factions
            ]
        return [
            unit for unit in self.get_units()
            if unit.get_faction() == factions
        ]

    def get_neighboring_hexes(self, hex: Hex) -> List[Hex]:
        neighbors = []
        directions = (
            self.EVEN_R_DIRECTIONS
            if hex.column % 2 == 0
            else self.ODD_R_DIRECTIONS
        )

        for dr, dq in directions:
            r = hex.row + dr
            q = hex.column + dq
            neighbor = self.get_hex(r, q)
            if neighbor:
                neighbors.append(neighbor)

        return neighbors

    def get_reachable_hexes(
            self, unit: Unit, start: Hex, move_points: int = None
    ) -> Set[Hex]:
        """Get all hexes reachable by the unit from the start hex."""
        if move_points is None:
            move_points = unit.get_move()

        visited = set()
        queue = deque()
        reachable_hexes = set()

        queue.append((start, 0))
        visited.add((start.row, start.column))
        reachable_hexes.add(start)

        while queue:
            current_hex, cost = queue.popleft()

            if cost >= move_points:
                continue

            if self.enemy_adjacent(unit, current_hex):
                # Movement must stop when entering a hex adjacent to an enemy
                # unit, so do not expand further from this hex.
                continue

            for neighbor in self.get_neighboring_hexes(current_hex):
                coord = (neighbor.row, neighbor.column)
                if coord not in visited:
                    visited.add(coord)
                    reachable_hexes.add(neighbor)
                    # TODO static cost of 1
                    queue.append((neighbor, cost + 1))

        return reachable_hexes

    def shortest_path(
            self, unit: Unit, start: Hex, end: Hex
    ) -> List[Hex]:
        """Find the shortest path from start to end hex for the unit."""
        move_points = unit.get_move()
        reachable_hexes = self.get_reachable_hexes(unit, start, move_points)

        if end not in reachable_hexes:
            return []

        visited = set()
        queue = deque([(start, [])])
        visited.add((start.row, start.column))

        while queue:
            current_hex, path = queue.popleft()
            new_path = path + [current_hex]

            if current_hex == end:
                return new_path

            if self.enemy_adjacent(unit, current_hex):
                # Cannot continue moving once adjacent to an enemy unit
                continue

            for neighbor in self.get_neighboring_hexes(current_hex):
                if (
                    (neighbor.row, neighbor.column) not in visited
                    and neighbor in reachable_hexes
                ):
                    visited.add((neighbor.row, neighbor.column))
                    queue.append((neighbor, new_path))

        return []

    def enemy_adjacent(self, unit: Unit, hex: Hex) -> bool:
        """Check if there are any enemy units adjacent to the given hex."""
        neighbor_hexes = self.get_neighboring_hexes(hex)
        neighbor_units = self.get_units_for_hexes(neighbor_hexes)

        for neighbor_unit in neighbor_units:
            if not neighbor_unit.is_friendly(unit):
                return True

        return False

    def hex_distance(friendly_hex, enemy_hex) -> int:
        """
        Calculate the hex distance between two hexes taking into account the
        even-r offset hex grid layout.
        """
        if friendly_hex is None or enemy_hex is None:
            raise ValueError("hex arguments must not be None")

        def to_cube(hex_obj: Hex) -> tuple[int, int, int]:
            """Convert offset coordinates to cube coordinates (odd-q)."""
            col = hex_obj.column
            row = hex_obj.row
            x = col
            z = row - (col - (col & 1)) // 2
            y = -x - z
            return x, y, z

        ax, ay, az = to_cube(friendly_hex)
        bx, by, bz = to_cube(enemy_hex)

        return max(abs(ax - bx), abs(ay - by), abs(az - bz))

    def get_nearest_enemy_unit(self, unit: Unit) -> Unit | None:
        """
        Return the closest enemy unit to the given unit.
        If no enemy units are found, returns None.
        """
        if unit is None or unit.get_coords() is None:
            return None

        own_faction = unit.get_faction()
        row, column = unit.get_coords()
        start_hex = self.get_hex(row, column)

        if start_hex is None:
            return None

        min_distance = float("inf")
        nearest_enemy = None

        for other in self.get_units():
            if other == unit or other.get_faction() == own_faction:
                continue

            if other.get_coords() is None:
                continue

            other_hex = self.get_hex(*other.get_coords())
            if other_hex is None:
                continue

            distance = Board.hex_distance(start_hex, other_hex)
            if distance < min_distance:
                min_distance = distance
                nearest_enemy = other

        return nearest_enemy

    def path_towards(
        self, unit: Unit, target_hex: Hex, max_steps: int
    ) -> List[Hex]:
        """Return a truncated shortest path from the unit to ``target_hex``."""
        if unit.get_coords() is None:
            return []

        start_hex = self.get_hex(*unit.get_coords())
        if start_hex is None:
            return []

        reachable = self.get_reachable_hexes(
            unit, start_hex, move_points=max_steps
        )
        if not reachable:
            return [start_hex]

        best = min(
            reachable, key=lambda h: Board.hex_distance(h, target_hex)
        )

        full_path = self.shortest_path(unit, start_hex, best)
        if not full_path:
            return [start_hex]

        return full_path[: max_steps + 1]

    def path_away_from(
        self, unit: Unit, threat_hex: Hex, max_steps: int
    ) -> List[Hex]:
        """Return a path that increases distance from ``threat_hex``."""
        if unit.get_coords() is None:
            return []

        start_hex = self.get_hex(*unit.get_coords())
        if start_hex is None:
            return []

        reachable = self.get_reachable_hexes(
            unit, start_hex, move_points=max_steps
        )
        if not reachable:
            return [start_hex]

        farthest = max(
            reachable, key=lambda h: Board.hex_distance(h, threat_hex)
        )

        path = self.shortest_path(unit, start_hex, farthest)
        if not path:
            return [start_hex]

        return path[: max_steps + 1]

    def get_units_for_hexes(self, hexes: List[Hex]) -> List[Unit]:
        units = []
        for unit in self.units.values():
            if unit.get_coords() in hexes:
                units.append(unit)
        return units

    def to_board_model(self) -> BoardModel:
        units = [unit.to_unit_model() for unit in self.get_units()]
        return BoardModel(rows=self.rows, columns=self.columns, units=units)

    def to_sparse_board(self) -> SparseBoard:
        units = [unit.to_sparse_unit() for unit in self.get_units()]
        return SparseBoard(units=units)
