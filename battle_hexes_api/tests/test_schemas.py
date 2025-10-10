import unittest

from battle_hexes_api.schemas import ScenarioModel
from battle_hexes_core.scenario.scenario import Scenario


class TestScenarioModel(unittest.TestCase):
    def test_round_trip(self):
        core_scenario = Scenario(id="s1", name="Scenario 1")

        model = ScenarioModel.from_core(core_scenario)
        self.assertEqual(model.id, "s1")
        self.assertEqual(model.name, "Scenario 1")

        converted = model.to_core()
        self.assertEqual(converted, core_scenario)
