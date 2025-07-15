from pydantic import BaseModel


class SparseUnit(BaseModel):
    id: str
    row: int
    column: int
