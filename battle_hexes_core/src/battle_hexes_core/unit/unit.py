from pydantic import BaseModel
import uuid
from battle_hexes_core.game.player import Player
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.sparseunit import SparseUnit


class UnitModel(BaseModel):
    id: uuid.UUID
    name: str
    faction_id: uuid.UUID
    type: str
    attack: int
    defense: int
    move: int
    row: int
    column: int


class Unit:
    def __init__(
            self,
            id: uuid.UUID,
            name: str,
            faction: Faction,
            player: Player,
            type: str,
            attack: int,
            defense: int,
            move: int,
            row: int = None,
            column: int = None):
        self.id = id
        self.name = name
        self.faction = faction
        self._player = player
        self.type = type
        self.attack = attack
        self.defense = defense
        self.move = move
        self.row = row
        self.column = column

    @property
    def player(self) -> Player:
        return self._player

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_faction(self):
        return self.faction

    def get_type(self):
        return self.type

    def get_attack(self):
        return self.attack

    def get_defense(self):
        return self.defense

    def get_strength(self) -> int:
        """The sum of the unit's attack and defense factors."""
        return self.attack + self.defense

    def get_move(self):
        return self.move

    def set_coords(self, row: int, column: int):
        self.row = row
        self.column = column

    def get_coords(self) -> tuple:
        if self.row is None and self.column is None:
            return None
        return (self.row, self.column)

    def is_friendly(self, other_unit: 'Unit') -> bool:
        """Check if the other unit's faction is owned by the player."""
        return self.player == other_unit.player

    def is_adjacent(self, other_unit) -> bool:
        # Even-Q Offset rules
        # https://www.redblobgames.com/grids/hexagons/
        even_q_offsets = [(-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1)]
        odd_q_offsets = [(1, 0), (1, 1), (0, 1), (-1, 0), (0, -1), (1, -1)]

        offsets = even_q_offsets if self.column % 2 == 0 else odd_q_offsets
        return any(
            (
                self.row + dr == other_unit.row and
                self.column + dc == other_unit.column
            )
            for dr, dc in offsets
        )

    def forced_move(
            self,
            board,
            from_hex: tuple[int, int],
            distance: int
    ) -> bool:
        """Move the unit away from ``from_hex``.

        Returns ``True`` when the retreat completes successfully.

        If the path is blocked by an enemy unit or leaves the board, the unit's
        coordinates are restored and ``False`` is returned.
        """
        if from_hex is None or self.row is None or self.column is None:
            return True

        original_position = (self.row, self.column)

        def to_cube(row: int, col: int) -> tuple[int, int, int]:
            x_coord = col
            z_coord = row - (col - (col & 1)) // 2
            y_coord = -x_coord - z_coord
            return x_coord, y_coord, z_coord

        def to_offset(
                x_coord: int,
                y_coord: int,
                z_coord: int,
        ) -> tuple[int, int]:
            column = x_coord
            row = z_coord + (column - (column & 1)) // 2
            return row, column

        origin_cube = to_cube(*from_hex)
        current_cube = to_cube(self.row, self.column)
        direction = tuple(
            current - origin
            for current, origin in zip(current_cube, origin_cube)
        )

        step_magnitude = max(abs(component) for component in direction)
        if step_magnitude == 0:
            self.row, self.column = original_position
            return False

        direction = tuple(
            component // step_magnitude for component in direction
        )

        for _ in range(distance):
            next_cube = tuple(
                current + delta
                for current, delta in zip(current_cube, direction)
            )
            next_row, next_col = to_offset(*next_cube)

            if not board.is_in_bounds(next_row, next_col):
                self.row, self.column = original_position
                return False

            occupant = board.get_unit_at(next_row, next_col)
            if occupant and not occupant.is_friendly(self):
                self.row, self.column = original_position
                return False

            self.row, self.column = next_row, next_col
            current_cube = next_cube

        return True

    def to_unit_model(self) -> UnitModel:
        return UnitModel(id=self.id,
                         name=self.name,
                         faction_id=self.faction.id,
                         type=self.type,
                         attack=self.attack,
                         defense=self.defense,
                         move=self.move,
                         row=self.row,
                         column=self.column)

    def to_sparse_unit(self) -> SparseUnit:
        return SparseUnit(id=str(self.id), row=self.row, column=self.column)

    def __str__(self):
        return f"{self.name} ({self.faction.name}) " + \
               f"{self.attack}-{self.defense}-{self.move}"
