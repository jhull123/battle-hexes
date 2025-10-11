from .scenario import Scenario
from .scenario_loader import iter_scenario_data


class ScenarioRegistry:
    def __init__(self):
        self._scenarios = {}
        for scenario_data in iter_scenario_data():
            scenario = Scenario(id=scenario_data.id, name=scenario_data.name)
            self._scenarios[scenario.id] = scenario

    def list_scenarios(self):
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> Scenario:
        """Return the scenario registered for ``scenario_id``."""

        try:
            return self._scenarios[scenario_id]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise KeyError(f"Scenario '{scenario_id}' not found") from exc
