"""Immutable v2 scenario and shared slot identities for training and play."""

from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario_loader import load_scenario_data


SCENARIO_ID = "ppo_9x9_experimental"
CONTRACT = "battle-hexes-9x9-2slot-unit-destination-live-turnlimit50-v2"
SLOT_IDS = ("learner-0", "learner-1", "opponent-0", "opponent-1")
TURN_LIMIT = 50


class LocalPlayer(Player):
    def combat_results(self, combat_results):
        pass


def scenario_data():
    return load_scenario_data(SCENARIO_ID)


def validate_scenario(scenario=None):
    scenario = scenario or scenario_data()
    if (scenario.id != SCENARIO_ID or scenario.version != "1"
            or scenario.turn_limit != TURN_LIMIT
            or tuple(unit.id for unit in scenario.units) != SLOT_IDS):
        raise ValueError("Incompatible playable PPO scenario or slot mapping")
    return scenario


def slots_for_game(game):
    """Include eliminated units using their stable known-unit identities."""
    units = {unit.id: unit for unit in game.board.get_known_units()}
    if set(units) != set(SLOT_IDS):
        raise ValueError("Incompatible PPO roster")
    return tuple(units[unit_id] for unit_id in SLOT_IDS)


def create_game(rng):
    scenario = validate_scenario().to_core()
    players = [LocalPlayer(name, PlayerType.CPU, [])
               for name in ("Learner", "Opponent")]
    _, _, _, game = GameCreator().build_game_components(scenario, players)
    game.defensive_fire_resolver.rng = rng
    game.scenario_id = SCENARIO_ID
    game.scenario_version = "1"
    return game, players[0], players[1], slots_for_game(game)
