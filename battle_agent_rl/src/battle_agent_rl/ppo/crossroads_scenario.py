"""Crossroads is the first supported task for reusable PPO decisions."""

from .decision_contract import ObservationBounds, ScenarioTask
from .decision_binding import slots_for_game as bind_slots
from .scenario_binding import (
    bind_task, create_task_game,
    validate_scenario as validate_task_scenario,
)


TASK = ScenarioTask(
    scenario_id="d_day_crossroads", scenario_version="1",
    # Pinned gameplay; never recompute this from a possibly changed file.
    gameplay_sha256=(
        "ee12cab7351b51f69b48f17f8a7774a3c037d7832310302b31a18c5d613c6782"),
    contract=("battle-hexes-crossroads-wehrmacht-unit-destination-"
              "live-turnlimit8-v1"),
    learner_seat=1,
    learner_ids=("A / Inf. Zug", "B / Inf. Zug", "Crossroads Feldwache",
                 "MG Trupp A", "StuG. III Zug A"),
    opponent_ids=tuple(f"Airborne Inf. {c}" for c in "ABCDEF"),
    bounds=ObservationBounds(
        unit_stats_high=7, movement_high=7, terrain_low=-2, terrain_high=3,
        road_high=1, objective_points_high=1, score_high=3,
        reinforcement_high=17),
)
GAMEPLAY_SHA256 = TASK.gameplay_sha256


def validate_scenario(scenario=None):
    return validate_task_scenario(TASK, scenario)


def slots_for_game(game):
    return bind_slots(game, TASK.learner_ids + TASK.opponent_ids)


def bind_game(game, learner, scenario=None):
    return bind_task(game, learner, TASK, scenario)


def create_game(rng):
    return create_task_game(TASK, rng)
