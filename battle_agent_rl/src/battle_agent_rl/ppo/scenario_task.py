"""Scenario-derived configuration, separate from live decision machinery."""

from dataclasses import dataclass, field

from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario_loader import ScenarioData
from battle_hexes_core.scenario.scenario_validator import ScenarioValidator

from .decision_binding import bind_decision, slots_for_game
from .decision_bounds import bounds_for_game, validate_dimensions
from .decision_contract import DecisionSpec
from .playable_scenario import LocalPlayer


def build_scenario_game(scenario):
    """Core creates configuration and identities; never advance or score it."""
    validate_dimensions(scenario.board_size, scenario.turn_limit)
    ScenarioValidator().validate(scenario.to_core())
    ids = tuple(u.id for u in scenario.units)
    if len(set(ids)) != len(ids):
        raise ValueError("Decision roster requires unique unit identities")
    players = [LocalPlayer(name, PlayerType.HUMAN, [])
               for name in ("Player 1", "Player 2")]
    try:
        game = GameCreator().build_game_components(
            scenario.to_core(), players)[-1]
        slots_for_game(game, ids)
    except (NameError, KeyError, IndexError, TypeError) as error:
        raise ValueError(f"Unsupported decision scenario: {error}") from error
    return game


def _decision_spec(scenario, learner_seat):
    if learner_seat not in (0, 1):
        raise ValueError("Decision learner seat must be 0 or 1")
    game = build_scenario_game(scenario)
    # All scenario units, not board population: includes undeployed reserves.
    slots = slots_for_game(game, tuple(u.id for u in scenario.units))
    rosters = [tuple(sorted(u.id for u in slots if u.player is player))
               for player in game.players]
    if any(not roster for roster in rosters):
        raise ValueError("Decision inputs need a nonempty roster per player")
    spec = DecisionSpec(
        scenario.board_size, learner_seat, rosters[learner_seat],
        rosters[1 - learner_seat],
        tuple(o.coords for o in scenario.objectives or ()),
        tuple(g.id for g in scenario.reinforcements or ()),
        scenario.turn_limit, bounds_for_game(game, slots))
    bind_decision(game, spec)
    return spec


@dataclass(frozen=True)
class ScenarioTask:
    """Loaded scenario snapshot plus PPO choices; no copied gameplay facts."""

    scenario: ScenarioData
    learner_seat: int
    contract: str
    spec: DecisionSpec = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "spec", _decision_spec(
            self.scenario, self.learner_seat))

    @property
    def scenario_id(self):
        return self.scenario.id

    @property
    def scenario_version(self):
        return self.scenario.version

    def decision_spec(self, scenario=None):
        return (self.spec if scenario is None else
                _decision_spec(scenario, self.learner_seat))
