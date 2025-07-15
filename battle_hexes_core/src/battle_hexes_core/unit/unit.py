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
            from_hex: tuple[int, int],
            distance: int
    ) -> None:
        """Moves the unit away from the given hex in Even-r Offset."""
        from_row, from_col = from_hex

        if self.column == from_col:
            self.row += (self.row - from_row) * distance
            return

        delta_col = self.column - from_col

        for i in range(0, distance):
            # same row = change
            # not same row, stay the same!
            if self.row == from_row:
                delta_row = - delta_col
            else:
                delta_row = 0

            from_row = self.row
            from_col = self.column

            self.row += delta_row
            self.column += delta_col

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
