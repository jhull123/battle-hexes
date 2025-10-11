from pydantic import BaseModel


class Faction(BaseModel):
    id: str
    name: str
    color: str

    def __eq__(self, other):
        return isinstance(other, Faction) and self.id == other.id
