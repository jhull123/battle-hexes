"""Core-loaded task binding with structural, not exact-gameplay checks."""

from .decision_binding import bind_decision
from .scenario_task import build_scenario_game


def validate_scenario(task, scenario=None):
    scenario = task.scenario if scenario is None else scenario
    task.decision_spec(scenario)
    return scenario


def bind_task(game, learner, task, scenario=None):
    """Require configured seat, identities, shapes and numeric interface."""
    spec = task.decision_spec(scenario)
    binding = bind_decision(game, spec)
    if learner is not binding.learner:
        raise ValueError("Incompatible decision learner seat")
    return binding


def create_task_game(task, rng, scenario=None):
    """Raw core state, not an environment reset or scoring workflow."""
    scenario = task.scenario if scenario is None else scenario
    game = build_scenario_game(scenario)
    game.scenario_version = scenario.version
    game.defensive_fire_resolver.rng = rng
    return bind_task(game, game.players[task.learner_seat], task, scenario)
