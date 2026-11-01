"""Permanent roster and explicit player/scoring roles over live core state."""

from dataclasses import dataclass

from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player
from battle_hexes_core.game.reinforcement import ReinforcementGroup
from battle_hexes_core.unit.unit import Unit

from .decision_contract import DecisionSpec


@dataclass(frozen=True)
class DecisionBinding:
    game: Game
    spec: DecisionSpec
    learner: Player
    opponent: Player
    scoring_player: Player | None
    slots: tuple[Unit, ...]
    reinforcement_groups: tuple[ReinforcementGroup, ...]

    @property
    def learner_slots(self):
        return self.slots[:len(self.spec.learner_ids)]

    @property
    def objective_coords(self):
        return self.spec.objective_coords


def slots_for_game(game, slot_ids):
    """History retains casualties; all groups retain undeployed identities."""
    units = {unit.id: unit for unit in game.board.get_known_units()}
    for group in game.reinforcements_deployer.groups:
        for unit in group.units:
            if unit.id in units and units[unit.id] is not unit:
                raise ValueError("Conflicting unit identities")
            units[unit.id] = unit
    if set(units) != set(slot_ids):
        raise ValueError("Incompatible decision roster")
    return tuple(units[unit_id] for unit_id in slot_ids)


def bind_decision(game, spec):
    """Bind configured identities/roles; scenario rule checks are separate."""
    if (len(game.players) != 2 or game.turn_limit != spec.turn_limit
            or (game.board.rows, game.board.columns) != spec.board_size):
        raise ValueError("Incompatible decision board, players or horizon")
    learner = game.players[spec.learner_seat]
    opponent = game.players[1 - spec.learner_seat]
    slots = slots_for_game(game, spec.slot_ids)
    owners = ((learner,) * len(spec.learner_ids) +
              (opponent,) * len(spec.opponent_ids))
    if any(unit.player is not owner for unit, owner in zip(slots, owners)):
        raise ValueError("Incompatible decision roster owners")
    groups = {g.id: g for g in game.reinforcements_deployer.groups}
    if (len(groups) != len(game.reinforcements_deployer.groups)
            or set(groups) != set(spec.reinforcement_ids)):
        raise ValueError("Incompatible reinforcement identities")
    return DecisionBinding(
        game, spec, learner, opponent, _scoring_player(game, spec), slots,
        tuple(groups[group_id] for group_id in spec.reinforcement_ids))


def _scoring_player(game, spec):
    """Resolve core's scoring_side metadata, independently of learner seat."""
    victory = getattr(game, "victory", None)
    if victory is not None and victory.method == "objective_control":
        for player in game.players:
            if any(victory.scoring_side in (f.id, f.name)
                   for f in player.factions):
                return player
    if spec.objective_coords:
        raise ValueError("Objective inputs require a core scoring-side rule")
    return None
