"""Board-related Pydantic schemas used by the API."""

from typing import TYPE_CHECKING

from pydantic import BaseModel

from .terrain import TerrainSummaryModel
from .unit import UnitModel

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.board import Board
    from battle_hexes_core.scenario.scenario import Scenario


class RoadPathCoordinateModel(BaseModel):
    """Coordinate point for a serialized road path."""

    row: int
    column: int


class RoadPathModel(BaseModel):
    """Serialized representation of a road path."""

    type: str
    path: list[RoadPathCoordinateModel]


class BoardModel(BaseModel):
    """Serialized representation of the in-memory board."""

    rows: int
    columns: int
    units: list[UnitModel]
    terrain: TerrainSummaryModel
    road_types: dict[str, float]
    road_paths: list[RoadPathModel]

    @classmethod
    def from_board(
        cls, board: "Board", scenario: "Scenario | None" = None
    ) -> "BoardModel":
        """Create a ``BoardModel`` from the core ``Board`` instance."""

        units = [UnitModel.from_unit(unit) for unit in board.get_units()]
        if scenario is None:
            terrain = TerrainSummaryModel()
        else:
            terrain = TerrainSummaryModel.from_board_and_scenario(
                board, scenario
            )
        return cls(
            rows=board.get_rows(),
            columns=board.get_columns(),
            units=units,
            terrain=terrain,
            road_types=board.get_road_types(),
            road_paths=[
                RoadPathModel(
                    type=road_type,
                    path=[
                        RoadPathCoordinateModel(row=row, column=column)
                        for row, column in path
                    ],
                )
                for road_type, path in board.get_road_paths()
            ],
        )
