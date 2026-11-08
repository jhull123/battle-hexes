"""Real-core fixtures for the partial Crossroads state/action contract."""

import random

import pytest

from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer
from battle_hexes_core.scenario.scenario_loader import ScenarioData

from battle_agent_rl.ppo.scenario_task import ScenarioTask


@pytest.fixture
def crossroads_task():
    return ScenarioTask.load("d_day_crossroads", learner_seat=1)


@pytest.fixture
def crossroads(crossroads_task):
    return crossroads_task.create_game(random.Random(17))


@pytest.fixture
def close_unopposed_side():
    def close(game):
        game.end_movement()
        assert game.current_phase == "end_turn"
        ObjectiveScorer().recalculate_scenario_victory(game)
        game.end_turn()
    return close


@pytest.fixture
def german_decision(crossroads, close_unopposed_side):
    close_unopposed_side(crossroads.game)
    return crossroads


@pytest.fixture
def small_scenario():
    return ScenarioData.model_validate({
        "id": "internal-reuse-fixture", "version": "test-only",
        "name": "Reuse fixture", "description": "Decision contract probe",
        "board_size": [5, 7], "turn_limit": 4, "stacking_limit": 1,
        "victory": {"method": "objective_control", "scoring_side": "Red"},
        "factions": [
            {"id": color, "name": color, "color": color, "player": seat}
            for color, seat in (("Red", "Player 1"), ("Blue", "Player 2"))],
        "units": [
            {"id": name, "name": name, "faction": faction, "type": "Infantry",
             "attack": 2, "defense": 1, "movement": move}
            for name, faction, move in (("Scout", "Red", 3),
                                        ("Support", "Red", 0),
                                        ("Guard", "Blue", 2),
                                        ("Reserve", "Blue", 1))],
        "hex_data": [
            {"coords": [4, 0], "units": ["Scout"]},
            {"coords": [0, 6], "units": ["Guard"]},
            {"coords": [3, 0], "terrain": "rough"}],
        "terrain_types": {"rough": {
            "color": "gray", "move_cost": 2, "combat_odds_shift": -1}},
        "road_types": {"track": {"edge_move_cost": 0.5}},
        "roads": [{"type": "track", "path": [[4, 0], [3, 0]]}],
        "objectives": [{"coords": coords, "points": 1, "type": "occupy"}
                       for coords in ([3, 1], [1, 5])],
        "reinforcements": [
            {"id": name, "units": [unit], "arrival_turn": 2,
             "entry_location": {"mode": "fixed", "coords": coords}}
            for name, unit, coords in (("blue-wave", "Reserve", [0, 5]),
                                       ("red-wave", "Support", [4, 1]))],
    })
