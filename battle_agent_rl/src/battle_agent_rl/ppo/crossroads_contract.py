"""Concrete task spaces; mechanics live in scenario-independent modules."""

from . import decision_contract
from .crossroads_scenario import TASK


CONTRACT = TASK.contract
SCENARIO_ID = TASK.scenario_id
SCENARIO_VERSION = TASK.scenario_version
LEARNER_IDS = TASK.spec.learner_ids
SLOT_IDS = TASK.spec.slot_ids


def observation_space(scenario=None):
    return decision_contract.observation_space(
        TASK.decision_spec(scenario))


def action_space(scenario=None):
    return decision_contract.action_space(
        TASK.decision_spec(scenario))
