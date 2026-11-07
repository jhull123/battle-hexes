"""Crossroads is the first supported task for reusable PPO decisions."""

from battle_hexes_core.scenario.scenario_loader import load_scenario_data

from .scenario_task import ScenarioTask
from .decision_binding import slots_for_game as bind_slots
from .scenario_binding import (
    bind_task, create_task_game,
    validate_scenario as validate_task_scenario,
)


TASK = ScenarioTask(
    scenario=load_scenario_data("d_day_crossroads"),
    contract="battle-hexes-unit-destination-live-v2",
    learner_seat=1,
)


def validate_scenario(scenario=None):
    return validate_task_scenario(TASK, scenario)


def slots_for_game(game, scenario=None):
    return bind_slots(game, TASK.decision_spec(scenario).slot_ids)


def bind_game(game, learner, scenario=None):
    return bind_task(game, learner, TASK, scenario)


def create_game(rng, scenario=None):
    return create_task_game(TASK, rng, scenario)
