"""Core-loaded Crossroads compatibility and permanent roster binding."""

from dataclasses import dataclass
import hashlib
import json

from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario_loader import load_scenario_data
from battle_hexes_core.scenario.scenario_validator import ScenarioValidator

from .crossroads_contract import SCENARIO_ID, SCENARIO_VERSION, SLOT_IDS
from .playable_scenario import LocalPlayer


# Pinned gameplay, not a fingerprint recomputed from a possibly changed file.
GAMEPLAY_SHA256 = (
    "ee12cab7351b51f69b48f17f8a7774a3c037d7832310302b31a18c5d613c6782")


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
    payload["hex_data"].sort(key=lambda item: item["coords"])
    return _digest(payload)


def _digest(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_scenario(scenario=None):
    scenario = (load_scenario_data(SCENARIO_ID)
                if scenario is None else scenario)
    if (scenario.id != SCENARIO_ID or scenario.version != SCENARIO_VERSION
            or gameplay_fingerprint(scenario) != GAMEPLAY_SHA256):
        raise ValueError("Incompatible Crossroads scenario gameplay")
    ScenarioValidator().validate(scenario.to_core())
    return scenario


def _build_game(scenario):
    players = [LocalPlayer(name, PlayerType.HUMAN, [])
               for name in ("Player 1", "Player 2")]
    return GameCreator().build_game_components(
        scenario.to_core(), players)[-1]


def slots_for_game(game):
    """Board history retains casualties; groups retain undeployed units."""
    units = {unit.id: unit for unit in game.board.get_known_units()}
    for group in game.reinforcements_deployer.groups:
        for unit in group.units:
            if unit.id in units and units[unit.id] is not unit:
                raise ValueError("Conflicting Crossroads unit identities")
            units[unit.id] = unit
    if set(units) != set(SLOT_IDS):
        raise ValueError("Incompatible Crossroads roster")
    return tuple(units[unit_id] for unit_id in SLOT_IDS)


def _rules(game, slots):
    """Immutable gameplay configuration, never live positions/readiness."""
    board = game.board
    players = game.get_players()
    return {
        "size": (board.rows, board.columns), "stacking": board.stacking_limit,
        "turn_limit": game.turn_limit,
        "victory": (game.victory.method, game.victory.scoring_side),
        "fire": vars(game.defensive_fire_resolver.settings),
        "factions": [sorted(f.id for f in p.factions) for p in players],
        "units": [(u.id, players.index(u.player), u.faction.id, u.type,
                   u.echelon, u.attack, u.defense, u.move,
                   u.defensive_fire_modifier) for u in slots],
        "terrain": [(h.terrain.move_cost, h.terrain.defensive_fire_modifier,
                     h.terrain.combat_odds_shift) for h in board.hexes],
        "roads": (board.get_road_types(), board.get_road_paths()),
        "objectives": [(o.coords, o.points, o.type)
                       for o in board.get_objectives()],
        "groups": [(g.id, tuple(u.id for u in g.units), g.arrival_turn,
                    g.coords) for g in game.reinforcements_deployer.groups],
    }


@dataclass(frozen=True)
class CrossroadsBinding:
    """Validated live references; the caller owns pending orders."""

    game: object
    learner: object
    opponent: object
    slots: tuple
    objective_coords: tuple

    @property
    def reinforcement_group(self):
        return self.game.reinforcements_deployer.groups[0]


def bind_game(game, learner, scenario=None):
    """Reject wrong sides/rules, without changing the supplied core game."""
    scenario = validate_scenario(scenario)
    reference = _build_game(scenario)
    try:
        slots = slots_for_game(game)
        compatible = (
            game.scenario_id == SCENARIO_ID
            and getattr(game, "scenario_version", SCENARIO_VERSION) ==
            SCENARIO_VERSION
            and len(game.players) == 2 and learner is game.players[1]
            and _rules(game, slots) == _rules(
                reference, slots_for_game(reference)))
    except (AttributeError, ValueError, IndexError, TypeError) as error:
        raise ValueError("Incompatible Crossroads game binding") from error
    if not compatible:
        raise ValueError("Incompatible Crossroads side or gameplay")
    return CrossroadsBinding(
        game, learner, game.players[0], slots,
        tuple(o.coords for o in scenario.objectives))


def create_game(rng):
    """Create raw Airborne-first core state, not an environment reset."""
    scenario = validate_scenario()
    game = _build_game(scenario)
    game.scenario_version = SCENARIO_VERSION
    game.defensive_fire_resolver.rng = rng
    return bind_game(game, game.players[1], scenario)
