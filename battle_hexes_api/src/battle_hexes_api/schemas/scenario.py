"""Pydantic schema for scenario resources."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from battle_hexes_core.scenario.scenario import Scenario


class ScenarioModel(BaseModel):
    """Pydantic representation of :class:`Scenario`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str

    @classmethod
    def from_core(cls, scenario: Scenario) -> "ScenarioModel":
        """Create a ``ScenarioModel`` from a core :class:`Scenario`."""

        return cls.model_validate(scenario)

    def to_core(self) -> Scenario:
        """Convert the Pydantic model back into a core :class:`Scenario`."""

        return Scenario(**self.model_dump())
