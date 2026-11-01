"""Task compatibility against core-loaded scenario gameplay, without turns."""

import hashlib
import json

from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario_loader import load_scenario_data
from battle_hexes_core.scenario.scenario_validator import ScenarioValidator

from .decision_binding import bind_decision
from .playable_scenario import LocalPlayer


def gameplay_fingerprint(scenario):
    payload = scenario.model_dump(mode="json")
    for key in ("name", "description"):
        payload.pop(key, None)
    if payload["victory"]:
        payload["victory"].pop("description", None)
    for faction in payload["factions"]:
        for key in ("name", "color", "sounds"):
            faction.pop(key, None)
    for unit in payload["units"]:
        unit.pop("name", None)
    for terrain in (payload["terrain_types"] or {}).values():
        terrain.pop("color", None)
    for key in ("units", "factions"):
        payload[key].sort(key=lambda item: item["id"])
    if payload["hex_data"]:
        payload["hex_data"].sort(key=lambda item: item["coords"])
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_scenario(task, scenario=None):
    scenario = (load_scenario_data(task.scenario_id)
                if scenario is None else scenario)
    if (scenario.id != task.scenario_id
            or scenario.version != task.scenario_version
            or gameplay_fingerprint(scenario) != task.gameplay_sha256):
        raise ValueError("Incompatible task scenario gameplay")
    ScenarioValidator().validate(scenario.to_core())
    return scenario


def _build_game(scenario):
    players = [LocalPlayer(name, PlayerType.HUMAN, [])
               for name in ("Player 1", "Player 2")]
    return GameCreator().build_game_components(
        scenario.to_core(), players)[-1]


def _rules(game, slots):
    """Immutable gameplay configuration, never live positions/readiness."""
    board = game.board
    players = game.get_players()
    victory = getattr(game, "victory", None)
    return {
        "size": (board.rows, board.columns), "stacking": board.stacking_limit,
        "turn_limit": game.turn_limit,
        "victory": (None if victory is None else
                    (victory.method, victory.scoring_side)),
        "fire": vars(game.defensive_fire_resolver.settings),
        "factions": [sorted(f.id for f in p.factions) for p in players],
        "units": [(u.id, players.index(u.player), u.faction.id, u.type,
                   u.echelon, u.attack, u.defense, u.move,
                   u.defensive_fire_modifier) for u in slots],
        "terrain": [None if h.terrain is None else
                    (h.terrain.move_cost, h.terrain.defensive_fire_modifier,
                     h.terrain.combat_odds_shift) for h in board.hexes],
        "roads": (board.get_road_types(), board.get_road_paths()),
        "objectives": [(o.coords, o.points, o.type)
                       for o in board.get_objectives()],
        "groups": [(g.id, tuple(u.id for u in g.units), g.arrival_turn,
                    g.coords) for g in game.reinforcements_deployer.groups],
    }


def bind_task(game, learner, task, scenario=None):
    """Reject wrong task/seat/rules before returning a reusable binding."""
    scenario = validate_scenario(task, scenario)
    spec = task.decision_spec(scenario)
    reference = bind_decision(_build_game(scenario), spec)
    try:
        binding = bind_decision(game, spec)
        compatible = (
            game.scenario_id == task.scenario_id
            and getattr(game, "scenario_version", task.scenario_version) ==
            task.scenario_version and learner is binding.learner
            and _rules(game, binding.slots) ==
            _rules(reference.game, reference.slots))
    except (AttributeError, ValueError, IndexError, TypeError) as error:
        raise ValueError("Incompatible task game binding") from error
    if not compatible:
        raise ValueError("Incompatible task side or gameplay")
    return binding


def create_task_game(task, rng):
    """Raw core state, not an environment reset or scoring workflow."""
    scenario = validate_scenario(task)
    game = _build_game(scenario)
    game.scenario_version = task.scenario_version
    game.defensive_fire_resolver.rng = rng
    return bind_task(game, game.players[task.learner_seat], task, scenario)
