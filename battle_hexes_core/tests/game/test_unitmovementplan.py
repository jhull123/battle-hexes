import unittest
from unittest.mock import MagicMock
from game.unitmovementplan import UnitMovementPlan
from game.hex import Hex


class TestUnitMovementPlan(unittest.TestCase):
    def test_to_dict(self):
        unit = MagicMock()
        unit.get_id.return_value = 'uid-1'
        plan = UnitMovementPlan(unit, [Hex(1, 2), Hex(2, 3)])
        expected = {
            'unit_id': 'uid-1',
            'path': [
                {'row': 1, 'column': 2},
                {'row': 2, 'column': 3},
            ],
        }
        self.assertEqual(plan.to_dict(), expected)
        unit.get_id.assert_called_once_with()
