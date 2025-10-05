from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
