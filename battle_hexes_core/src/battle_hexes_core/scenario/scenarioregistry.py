from .scenario import Scenario


class ScenarioRegistry:
    def __init__(self):
        s1 = Scenario(id="elem_1", name="Elimination Demo 1")
        s2 = Scenario(id="elem_2", name="Elimination Demo 2")
        self._scenarios = {
            s1.id: s1,
            s2.id: s2
        }

    def list_scenarios(self):
        return list(self._scenarios.values())
