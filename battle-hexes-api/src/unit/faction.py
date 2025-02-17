from pydantic import BaseModel
from uuid import UUID


class Faction(BaseModel):
    id: UUID
    name: str
    color: str

    def __eq__(self, other):
        return isinstance(other, Faction) and self.id == other.id
