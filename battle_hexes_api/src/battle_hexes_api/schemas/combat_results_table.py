"""Schemas for the authoritative combat results table reference."""

from pydantic import Field

from .api_model import ApiBaseModel


class CombatResultReferenceModel(ApiBaseModel):
    """Stable and display-ready representations of one combat result."""

    code: str
    text: str

    @classmethod
    def from_core(cls, result):
        return cls(code=result.name, text=result.value)


class CombatResultsTableRowModel(ApiBaseModel):
    """One normal or automatic CRT odds row."""

    odds: tuple[int, int]
    results: list[CombatResultReferenceModel] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    automatic_result: CombatResultReferenceModel | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @classmethod
    def from_core(cls, row):
        return cls(
            odds=row.odds,
            results=(
                [CombatResultReferenceModel.from_core(result)
                 for result in row.results]
                if row.results is not None
                else None
            ),
            automatic_result=(
                CombatResultReferenceModel.from_core(row.automatic_result)
                if row.automatic_result is not None
                else None
            ),
        )


class CombatResultsTableModel(ApiBaseModel):
    """Complete ordered CRT reference included in full game state."""

    die_rolls: list[int]
    rows: list[CombatResultsTableRowModel]

    @classmethod
    def from_core(cls, table):
        return cls(
            die_rolls=list(table.die_rolls),
            rows=[CombatResultsTableRowModel.from_core(row)
                  for row in table.rows],
        )
