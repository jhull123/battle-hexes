"""Real-core fixtures for the partial Crossroads state/action contract."""

import random

import pytest

from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from battle_agent_rl.ppo.crossroads_scenario import create_game


@pytest.fixture
def crossroads():
    return create_game(random.Random(17))


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
