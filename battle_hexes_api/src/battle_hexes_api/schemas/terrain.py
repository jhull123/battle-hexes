"""Schemas describing terrain data for the API."""

from typing import Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from battle_hexes_core.scenario.scenario import Scenario, ScenarioTerrainType

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from battle_hexes_core.game.board import Board


class TerrainTypeModel(BaseModel):
    """Representation of a terrain type."""

    name: str
    color: str
    move_cost: int = 1

    @classmethod
    def from_scenario_type(
        cls, name: str, terrain_type: ScenarioTerrainType
    ) -> "TerrainTypeModel":
        """Create a terrain type model from scenario data."""

        return cls(
            name=name,
            color=terrain_type.color,
            move_cost=terrain_type.move_cost,
        )


class TerrainHexModel(BaseModel):
    """Sparse terrain hex override used by the frontend."""

    row: int
    column: int
    terrain: str


class TerrainSummaryModel(BaseModel):
    """Container for terrain defaults, types, and hex overrides."""

    default: Optional[str] = None
    types: Dict[str, TerrainTypeModel] = Field(default_factory=dict)
    hexes: List[TerrainHexModel] = Field(default_factory=list)

    @classmethod
    def from_board_and_scenario(
        cls, board: "Board", scenario: Scenario
    ) -> "TerrainSummaryModel":
        """Build terrain metadata from a board and its scenario."""

        types = {
            name: TerrainTypeModel.from_scenario_type(name, terrain_type)
            for name, terrain_type in scenario.terrain_types.items()
        }
        default = scenario.terrain_default
        hexes = []
        for hex_tile in board.hexes:
            terrain = hex_tile.terrain
            if terrain is None:
                continue
            if default is not None and terrain.name == default:
                continue
            hexes.append(
                TerrainHexModel(
                    row=hex_tile.row,
                    column=hex_tile.column,
                    terrain=terrain.name,
                )
            )

        return cls(default=default, types=types, hexes=hexes)
