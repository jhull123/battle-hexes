"""Persisted, JSON-only PPO turn state and configured artifact access."""

import json
import logging
import random

from battle_agent_rl.ppo.playable_scenario import (CONTRACT, SCENARIO_ID,
                                                   SLOT_IDS, TURN_LIMIT)
from battle_hexes_api.persistence.errors import SavedGameIncompatibleError
from battle_hexes_api.ppo_artifact import configured_model


TYPE_ID = "ppo-9x9-experimental"
logger = logging.getLogger(__name__)


def is_ppo_game(game):
    return isinstance(getattr(game, "ppo_state", None), dict)


def initial_state(game):
    try:
        _, manifest = configured_model()
    except ValueError as error:
        from battle_hexes_api.persistence.command_errors import (
            CommandErrorTranslator,
        )
        raise CommandErrorTranslator.error(
            503, "ppoArtifactUnavailable") from error
    rng = random.Random()
    game.ppo_rng = rng
    game.defensive_fire_resolver.rng = rng
    game.ppo_state = {
        "contract": CONTRACT, "checkpoint_digest":
        manifest["checkpoint"]["sha256"],
        "checkpoint_path": manifest["checkpoint"]["path"],
        "pending_unit_ids": list(SLOT_IDS[:2]),
        "rng_state": json.loads(json.dumps(rng.getstate())),
    }


def _tuples(value):
    if isinstance(value, list):
        return tuple(_tuples(item) for item in value)
    return value


def validate_state(state, game_or_document):
    """Reject corrupt state before any prediction or core mutation."""
    player_types = (getattr(game_or_document, "player_type_ids", None) or
                    [player.type_id for player in game_or_document.players])
    scenario_id = game_or_document.scenario_id
    if (scenario_id != SCENARIO_ID or len(player_types) != 2
            or player_types[0] != TYPE_ID or player_types[1] == TYPE_ID):
        if state is not None or TYPE_ID in player_types:
            raise SavedGameIncompatibleError("ppo_scenario_or_seat")
        return
    if state is None:
        raise SavedGameIncompatibleError("ppo_state_missing")
    _validate_turn_state(state, game_or_document)
    return _restore_rng(state)


def _validate_turn_state(state, game_or_document):
    current_player = getattr(game_or_document, "current_player", None)
    player_name = (current_player.name if current_player is not None else
                   getattr(game_or_document, "current_player_name", None))
    active = (player_name == "Learner" and
              game_or_document.current_phase == "movement" and
              _status(game_or_document) == "in_progress")
    try:
        pending = state["pending_unit_ids"]
        living = _living_ids(game_or_document)
        valid = (state["contract"] == CONTRACT
                 and state["checkpoint_path"] == "checkpoint.zip"
                 and isinstance(state["checkpoint_digest"], str)
                 and len(state["checkpoint_digest"]) == 64
                 and getattr(game_or_document, "turn_limit", TURN_LIMIT) ==
                 TURN_LIMIT
                 and 1 <= game_or_document.turn_number <= TURN_LIMIT
                 and len(pending) == len(set(pending))
                 and all(unit_id in SLOT_IDS[:2] and unit_id in living
                         for unit_id in pending)
                 and _pending_ready(game_or_document, pending)
                 and bool(pending) == active)
        if not valid:
            raise ValueError("incompatible state")
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise SavedGameIncompatibleError("ppo_turn_state") from error


def _status(value):
    return (value.get_game_status().state if hasattr(value, "get_game_status")
            else value.game_status.state)


def _living_ids(value):
    if hasattr(value, "units"):
        return {unit.unit_id for unit in value.units
                if unit.disposition == "active"}
    return {unit.id for unit in value.board.get_units()}


def _pending_ready(value, pending):
    if hasattr(value, "units"):
        units = {unit.unit_id: unit for unit in value.units}
        return all(units[unit_id].movement_points_remaining == 2
                   for unit_id in pending)
    units = {unit.id: unit for unit in value.board.get_units()}
    return all(units[unit_id].current_turn_movement_points_remaining ==
               units[unit_id].move for unit_id in pending)


def _restore_rng(state):
    try:
        rng = random.Random()
        rng.setstate(_tuples(state["rng_state"]))
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise SavedGameIncompatibleError("ppo_rng_state") from error
    return rng


def restore_state(game, document):
    if document.ppo_state is None:
        return
    state = document.ppo_state.model_dump()
    rng = validate_state(state, game)
    try:
        _, manifest = configured_model(state["checkpoint_digest"])
        if state["checkpoint_path"] != manifest["checkpoint"]["path"]:
            raise ValueError("Checkpoint path mismatch")
    except ValueError as error:
        logger.error(
            "Saved PPO game %s cannot resume: checkpoint digest %s is no "
            "longer available in the configured artifact (%s)",
            game.id, state["checkpoint_digest"], error,
        )
        raise SavedGameIncompatibleError("ppo_artifact_unavailable") from error
    game.ppo_state = state
    game.ppo_rng = rng
    game.defensive_fire_resolver.rng = rng


def capture_rng(game):
    if is_ppo_game(game):
        game.ppo_state["rng_state"] = json.loads(
            json.dumps(game.ppo_rng.getstate()))
