"""Pydantic schema for scenario resources."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from battle_hexes_core.scenario.scenario import Scenario, ScenarioVictory


class ScenarioVictoryModel(BaseModel):
    """Pydantic representation of :class:`ScenarioVictory`."""

    model_config = ConfigDict(from_attributes=True)

    method: str
    scoring_side: str
    description: str | None = None


class ScenarioModel(BaseModel):
    """Pydantic representation of :class:`Scenario`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    victory: ScenarioVictoryModel | None = None
    stacking_limit: int | None = None

    @classmethod
    def from_core(cls, scenario: Scenario) -> "ScenarioModel":
        """Create a ``ScenarioModel`` from a core :class:`Scenario`."""

        return cls.model_validate(scenario)

    def to_core(self) -> Scenario:
        """Convert the Pydantic model back into a core :class:`Scenario`."""

        return Scenario(
            **self.model_dump(exclude={"victory"}),
            victory=(
                ScenarioVictory(**self.victory.model_dump())
                if self.victory is not None
                else None
            ),
        )
