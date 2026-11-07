"""Scenario-derived configuration, separate from live decision machinery."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario_loader import (
    ScenarioData, load_scenario_data,
)
from battle_hexes_core.scenario.scenario_validator import ScenarioValidator

from .decision_binding import bind_decision, slots_for_game
from .decision_bounds import bounds_for_game, validate_dimensions
from . import decision_contract
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
    """Data-driven decision interface; learner seat is a runtime choice.

    Accept core-loaded ScenarioData directly, or load() an ID/directory.
    A task fixes its spaces and complete roster for an episode, not a trained
    policy's compatibility with other scenarios. Creation/binding never
    advances turns, scores, executes orders or consumes RNG.
    """

    scenario: ScenarioData
    learner_seat: int
    contract: ClassVar[str] = decision_contract.CONTRACT
    spec: DecisionSpec = field(init=False)

    def __post_init__(self):
        # ScenarioData is shallow-frozen; isolate its nested lists/dicts from
        # editor changes so creation cannot drift from the derived interface.
        object.__setattr__(
            self, "scenario", self.scenario.model_copy(deep=True))
        object.__setattr__(self, "spec", _decision_spec(
            self.scenario, self.learner_seat))

    @classmethod
    def load(cls, scenario_id: str, *, learner_seat: int,
             scenario_dir: Path | None = None):
        """Use core's JSON loader without a PPO scenario registry."""
        return cls(load_scenario_data(scenario_id, scenario_dir=scenario_dir),
                   learner_seat)

    @property
    def scenario_id(self):
        return self.scenario.id

    @property
    def scenario_version(self):
        return self.scenario.version

    def create_game(self, rng):
        """Return a binding over raw core state, not an environment reset."""
        game = build_scenario_game(self.scenario)
        game.scenario_version = self.scenario_version
        game.defensive_fire_resolver.rng = rng
        return self.bind_game(game)

    def bind_game(self, game, learner=None):
        """Bind raw or advanced state by representation, not gameplay identity.

        The configured seat selects the learner. If supplied, a runtime player
        must match that seat; core's player order is never changed.
        """
        binding = bind_decision(game, self.spec)
        if learner is not None and learner is not binding.learner:
            raise ValueError("Incompatible decision learner seat")
        return binding

    def observation_space(self):
        return decision_contract.observation_space(self.spec)

    def action_space(self):
        return decision_contract.action_space(self.spec)
