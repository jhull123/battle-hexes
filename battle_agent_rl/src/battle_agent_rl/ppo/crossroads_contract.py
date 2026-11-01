"""Concrete task spaces; mechanics live in scenario-independent modules."""

from . import decision_contract
from .crossroads_scenario import TASK, validate_scenario


CONTRACT = TASK.contract
SCENARIO_ID = TASK.scenario_id
SCENARIO_VERSION = TASK.scenario_version
LEARNER_IDS = TASK.learner_ids
SLOT_IDS = LEARNER_IDS + TASK.opponent_ids


def observation_space():
    return decision_contract.observation_space(
        TASK.decision_spec(validate_scenario()))


def action_space():
    return decision_contract.action_space(
        TASK.decision_spec(validate_scenario()))
