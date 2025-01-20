from pydantic import BaseModel
from uuid import UUID


class Faction(BaseModel):
    id: UUID
    name: str
    color: str
