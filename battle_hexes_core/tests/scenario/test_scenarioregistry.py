import unittest
from battle_hexes_core.scenario.scenarioregistry import ScenarioRegistry
from battle_hexes_core.scenario.scenario import Scenario


class TestScenarioRegistry(unittest.TestCase):
    def test_list_scenarios(self):
        registry = ScenarioRegistry()
        scenarios = registry.list_scenarios()
        self.assertEqual(len(scenarios), 2)
        self.assertTrue(all(isinstance(s, Scenario) for s in scenarios))

        # Check for specific scenarios, order might not be guaranteed
        expected_ids = {"elim_1", "elim_2"}
        actual_ids = {s.id for s in scenarios}
        self.assertEqual(expected_ids, actual_ids)

        expected_names = {"Elimination Demo 1", "Elimination Demo 2"}
        actual_names = {s.name for s in scenarios}
        self.assertEqual(expected_names, actual_names)


if __name__ == '__main__':
    unittest.main()
