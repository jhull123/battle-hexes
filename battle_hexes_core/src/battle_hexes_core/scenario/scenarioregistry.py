from .scenario import Scenario
from .scenario_loader import iter_scenarios


class ScenarioRegistry:
    def __init__(self):
        self._scenarios = {}
        for scenario in iter_scenarios():
            self._scenarios[scenario.id] = scenario

    def list_scenarios(self):
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> Scenario:
        """Return the scenario registered for ``scenario_id``."""

        try:
            return self._scenarios[scenario_id]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise KeyError(f"Scenario '{scenario_id}' not found") from exc
