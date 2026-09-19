"""Canonical, safe serialization of authoritative game state."""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import asdict
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt

from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_core.combat.combat_event import (
    CombatEvent,
    CombatOutcomeSnapshot,
    CombatTerrainSnapshot,
    CombatUnitSnapshot,
)
from battle_hexes_core.defensivefire.defensive_fire_event import (
    DefensiveFireEvent,
    DefensiveFireUnitSnapshot,
)
from battle_hexes_core.game.reinforcement import ReinforcementArrivalEvent
from battle_hexes_core.gamecreator.gamecreator import (
    GameCreator as CoreCreator,
)
from battle_hexes_core.scenario.scenario_loader import (
    ScenarioData,
    load_scenario_data,
)
from battle_hexes_core.scoring.game_status_evaluator import GameStatus

from .contracts import StoredGame
from .errors import SavedGameIncompatibleError
from .identity import canonical_json_bytes


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _Player(_Model):
    name: str
    type_id: Literal["human", "random", "q-learning"]


class _PendingCombat(_Model):
    attacker_unit_ids: list[str]
    defender_unit_ids: list[str]


class _Status(_Model):
    state: Literal["in_progress", "completed"]
    winner_player_name: str | None
    winner_faction_id: str | None
    reason: str | None
    message: str | None


class _Score(_Model):
    player_name: str
    points: StrictInt


class _Unit(_Model):
    unit_id: str
    disposition: Literal["active", "reinforcement", "eliminated"]
    row: StrictInt | None
    column: StrictInt | None
    movement_points_remaining: StrictInt
    ended_last_friendly_turn_with_defensive_fire_eligibility: StrictBool
    forced_to_retreat_since_last_friendly_turn: StrictBool
    defensive_fire_spent_this_off_turn: StrictBool
    defensive_fire_available: StrictBool
    defensive_fire_modifier: float


class _Reinforcement(_Model):
    group_id: str
    entered: StrictBool


class _Document(_Model):
    state_schema_version: StrictInt
    game_id: str
    scenario_id: str
    scenario_version: str
    players: list[_Player]
    current_player_name: str | None
    turn_number: StrictInt
    current_phase: Literal["movement", "combat", "end_turn"] | None
    pending_combats: list[_PendingCombat]
    terminal: StrictBool
    game_status: _Status
    scores: list[_Score]
    active_unit_ids: list[str]
    units: list[_Unit]
    reinforcements: list[_Reinforcement]
    reinforcement_history: list[dict[str, Any]]
    combat_history: list[dict[str, Any]]
    defensive_fire_history: list[dict[str, Any]]


class GameStateCodec:
    """Encode games and hydrate detached games against immutable scenarios."""

    STATE_SCHEMA_VERSION = 1

    def __init__(
        self,
        scenario_loader: Callable[[str], ScenarioData] = load_scenario_data,
    ) -> None:
        self._scenario_loader = scenario_loader

    def encode(self, game, *, scenario_version: str) -> bytes:
        """Return a complete canonical version-1 state document."""
        try:
            scenario = self._load_scenario(game.scenario_id)
            if scenario.version != scenario_version:
                self._incompatible("scenario_version")
            document = self._encode_document(game, scenario, scenario_version)
            validated = _Document.model_validate(document)
            self._validate(validated, scenario)
            return canonical_json_bytes(document)
        except SavedGameIncompatibleError:
            raise
        except Exception as error:
            raise SavedGameIncompatibleError("invalid_game_graph") from error

    def decode(self, stored_game: StoredGame):
        """Validate and hydrate a detached game without running game rules."""
        try:
            if stored_game.state_schema_version != self.STATE_SCHEMA_VERSION:
                self._incompatible("schema_version")
            payload = json.loads(stored_game.state.decode("utf-8"))
            document = _Document.model_validate(payload)
            metadata = (
                document.game_id == stored_game.game_id
                and document.scenario_id == stored_game.scenario_id
                and document.scenario_version == stored_game.scenario_version
                and document.state_schema_version
                == stored_game.state_schema_version
            )
            if not metadata:
                self._incompatible("metadata")
            scenario = self._load_scenario(document.scenario_id)
            if scenario.version != document.scenario_version:
                self._incompatible("scenario_version")
            self._validate(document, scenario)
            return self._hydrate(document, scenario)
        except SavedGameIncompatibleError:
            raise
        except Exception as error:
            raise SavedGameIncompatibleError("invalid_state") from error

    def _load_scenario(self, scenario_id: str) -> ScenarioData:
        try:
            scenario = self._scenario_loader(scenario_id)
        except Exception as error:
            raise SavedGameIncompatibleError("scenario_missing") from error
        if not isinstance(scenario, ScenarioData):
            self._incompatible("scenario_invalid")
        return scenario

    def _encode_document(self, game, scenario, version):
        board_units = {
            str(unit.get_id()): unit for unit in game.board.get_units()
        }
        all_units = dict(board_units)
        pending_ids = set()
        for group in game.reinforcements_deployer.groups:
            for unit in group.units:
                all_units[str(unit.get_id())] = unit
                if not group.entered:
                    pending_ids.add(str(unit.get_id()))
        units = []
        for definition in scenario.units:
            unit = all_units[definition.id]
            disposition = (
                "active"
                if definition.id in board_units
                else (
                    "reinforcement"
                    if definition.id in pending_ids
                    else "eliminated"
                )
            )
            coords = unit.get_coords() if disposition == "active" else None
            movement = unit.current_turn_movement_points_remaining
            ended_eligible = (
                unit.ended_last_friendly_turn_with_defensive_fire_eligibility
            )
            forced_retreat = unit.forced_to_retreat_since_last_friendly_turn
            fire_spent = unit.defensive_fire_spent_this_off_turn
            units.append(
                {
                    "unit_id": definition.id,
                    "disposition": disposition,
                    "row": coords[0] if coords else None,
                    "column": coords[1] if coords else None,
                    "movement_points_remaining": movement,
                    "ended_last_friendly_turn_with_defensive_fire_eligibility": ended_eligible,  # noqa: E501
                    "forced_to_retreat_since_last_friendly_turn": forced_retreat,  # noqa: E501
                    "defensive_fire_spent_this_off_turn": fire_spent,
                    "defensive_fire_available": unit.defensive_fire_available,
                    "defensive_fire_modifier": unit.defensive_fire_modifier,
                }
            )
        status = game.get_game_status()
        return {
            "state_schema_version": self.STATE_SCHEMA_VERSION,
            "game_id": str(game.id),
            "scenario_id": game.scenario_id,
            "scenario_version": version,
            "players": [
                {"name": player.name, "type_id": type_id}
                for player, type_id in zip(game.players, game.player_type_ids)
            ],
            "current_player_name": (
                game.current_player.name if game.current_player else None
            ),
            "turn_number": game.turn_number,
            "current_phase": game.current_phase,
            "pending_combats": game.pending_combats,
            "terminal": game._terminal,
            "game_status": asdict(status),
            "scores": [
                {
                    "player_name": player.name,
                    "points": game.score_tracker.get_score(player),
                }
                for player in game.players
            ],
            "active_unit_ids": list(board_units),
            "units": units,
            "reinforcements": [
                {"group_id": group.id, "entered": group.entered}
                for group in game.reinforcements_deployer.groups
            ],
            "reinforcement_history": [
                asdict(event)
                for event in game.reinforcements_deployer.game_log
            ],
            "combat_history": [asdict(event) for event in game.combat_log],
            "defensive_fire_history": [
                asdict(event) for event in game.defensive_fire_log
            ],
        }

    def _validate(self, doc: _Document, scenario: ScenarioData) -> None:
        if doc.state_schema_version != self.STATE_SCHEMA_VERSION:
            self._incompatible("schema_version")
        if doc.game_id == "" or doc.scenario_id != scenario.id:
            self._incompatible("metadata")
        expected_players = []
        for faction in scenario.factions:
            if faction.player not in expected_players:
                expected_players.append(faction.player)
        names = [entry.name for entry in doc.players]
        if names != expected_players or len(names) != len(set(names)):
            self._incompatible("players")
        unit_ids = [unit.unit_id for unit in doc.units]
        expected_units = [unit.id for unit in scenario.units]
        if unit_ids != expected_units or len(unit_ids) != len(set(unit_ids)):
            self._incompatible("units")
        group_ids = [group.group_id for group in doc.reinforcements]
        expected_groups = [
            group.id for group in (scenario.reinforcements or [])
        ]
        if group_ids != expected_groups:
            self._incompatible("reinforcements")
        active = [
            unit.unit_id for unit in doc.units if unit.disposition == "active"
        ]
        if set(doc.active_unit_ids) != set(active) or len(
            doc.active_unit_ids
        ) != len(set(doc.active_unit_ids)):
            self._incompatible("active_units")
        pending_scenario_ids = {
            unit_id
            for group, state in zip(
                scenario.reinforcements or [], doc.reinforcements
            )
            if not state.entered
            for unit_id in group.units
        }
        for unit in doc.units:
            coords_valid = unit.row is not None and unit.column is not None
            if unit.disposition == "active":
                if not coords_valid or not (
                    0 <= unit.row < scenario.board_size[0]
                    and 0 <= unit.column < scenario.board_size[1]
                ):
                    self._incompatible("coordinates")
            elif unit.row is not None or unit.column is not None:
                self._incompatible("coordinates")
            if (unit.disposition == "reinforcement") != (
                unit.unit_id in pending_scenario_ids
            ):
                self._incompatible("disposition")
            if not math.isfinite(unit.defensive_fire_modifier):
                self._incompatible("numeric_value")
        if [score.player_name for score in doc.scores] != names or any(
            score.points < 0 for score in doc.scores
        ):
            self._incompatible("scores")
        if doc.turn_number < 1:
            self._incompatible("turn_number")
        if doc.terminal:
            if (
                doc.current_player_name is not None
                or doc.current_phase is not None
                or doc.pending_combats
                or doc.game_status.state != "completed"
            ):
                self._incompatible("terminal_state")
        elif (
            doc.current_player_name not in names
            or doc.current_phase is None
            or doc.game_status.state != "in_progress"
        ):
            self._incompatible("terminal_state")
        active_set = set(active)
        current_index = (
            names.index(doc.current_player_name)
            if doc.current_player_name
            else None
        )
        owner_by_unit = {
            unit.id: names.index(
                next(
                    faction.player
                    for faction in scenario.factions
                    if faction.id == unit.faction
                )
            )
            for unit in scenario.units
        }
        for combat in doc.pending_combats:
            attackers, defenders = (
                combat.attacker_unit_ids,
                combat.defender_unit_ids,
            )
            if (
                not attackers
                or not defenders
                or len(set(attackers)) != len(attackers)
                or len(set(defenders)) != len(defenders)
                or set(attackers) & set(defenders)
                or not set(attackers + defenders) <= active_set
                or current_index is None
                or any(owner_by_unit[x] != current_index for x in attackers)
                or any(owner_by_unit[x] == current_index for x in defenders)
            ):
                self._incompatible("pending_combats")
        self._validate_histories(doc, set(expected_units), set(names))

    def _validate_histories(self, doc, unit_ids, player_names):
        try:
            for value in doc.reinforcement_history:
                event = ReinforcementArrivalEvent(**value)
                if event.player_name not in player_names:
                    raise ValueError
                if not (
                    isinstance(event.entry_coordinate, (list, tuple))
                    and len(event.entry_coordinate) == 2
                ):
                    raise ValueError
            for value in doc.combat_history:
                self._combat_event(value, player_names)
            for value in doc.defensive_fire_history:
                event = self._defensive_event(value)
                if (
                    event.player_name not in player_names
                    or event.firing_unit.unit_id not in unit_ids
                    or event.target_unit.unit_id not in unit_ids
                    or not math.isfinite(event.success_probability)
                    or not math.isfinite(event.random_roll)
                ):
                    raise ValueError
        except (TypeError, ValueError, KeyError) as error:
            raise SavedGameIncompatibleError("history") from error

    def _hydrate(self, doc, scenario_data):
        players = [
            GameCreator._create_player(p.type_id, p.name, [], None)
            for p in doc.players
        ]
        _, players, _, game = CoreCreator().build_game_components(
            scenario_data.to_core(), players
        )
        game.id = uuid.UUID(doc.game_id)
        game.scenario_id = doc.scenario_id
        game.scenario_version = doc.scenario_version
        game.player_type_ids = [p.type_id for p in doc.players]
        all_units = {str(u.id): u for u in game.board.get_units()}
        for group in game.reinforcements_deployer.groups:
            all_units.update((str(u.id), u) for u in group.units)
        game.board.units = {}
        by_id = {unit.unit_id: unit for unit in doc.units}
        for unit_id in doc.active_unit_ids:
            saved, unit = by_id[unit_id], all_units[unit_id]
            game.board.add_unit(unit, saved.row, saved.column)
        for saved in doc.units:
            unit = all_units[saved.unit_id]
            if saved.disposition != "active":
                unit.set_coords(None, None)
            unit.current_turn_movement_points_remaining = (
                saved.movement_points_remaining
            )
            for attr in (
                "ended_last_friendly_turn_with_defensive_fire_eligibility",
                "forced_to_retreat_since_last_friendly_turn",
                "defensive_fire_spent_this_off_turn",
                "defensive_fire_available",
                "defensive_fire_modifier",
            ):
                setattr(unit, attr, getattr(saved, attr))
        for group, saved in zip(
            game.reinforcements_deployer.groups, doc.reinforcements
        ):
            group.entered = saved.entered
        game.turn_number = doc.turn_number
        game.current_player = next(
            (p for p in players if p.name == doc.current_player_name), None
        )
        game.current_phase = doc.current_phase
        game.pending_combats = [
            item.model_dump() for item in doc.pending_combats
        ]
        game._terminal = doc.terminal
        game.game_status = GameStatus(**doc.game_status.model_dump())
        game.score_tracker.set_scores(
            (player, score.points)
            for player, score in zip(players, doc.scores)
        )
        game.reinforcements_deployer.game_log = [
            ReinforcementArrivalEvent(
                **{
                    **value,
                    "entry_coordinate": tuple(value["entry_coordinate"]),
                }
            )
            for value in doc.reinforcement_history
        ]
        game.combat_log = [
            self._combat_event(
                value,
                set(doc.players[i].name for i in range(len(doc.players))),
            )
            for value in doc.combat_history
        ]
        game.defensive_fire_log = [
            self._defensive_event(value)
            for value in doc.defensive_fire_history
        ]
        for player in players:
            if hasattr(player, "_board"):
                player._board = game.board
        return game

    @staticmethod
    def _combat_event(value, player_names):
        value = dict(value)
        value["attackers"] = tuple(
            CombatUnitSnapshot(**x) for x in value["attackers"]
        )
        value["defenders"] = tuple(
            CombatUnitSnapshot(**x) for x in value["defenders"]
        )
        value["base_odds"] = tuple(value["base_odds"])
        value["modified_odds"] = tuple(value["modified_odds"])
        value["defender_terrain"] = CombatTerrainSnapshot(
            **value["defender_terrain"]
        )
        value["result"] = CombatOutcomeSnapshot(**value["result"])
        value["eliminated_units"] = tuple(value["eliminated_units"])
        value["retreated_units"] = tuple(value["retreated_units"])
        event = CombatEvent(**value)
        if event.player_name not in player_names:
            raise ValueError
        return event

    @staticmethod
    def _defensive_event(value):
        value = dict(value)
        value["firing_unit"] = DefensiveFireUnitSnapshot(
            **value["firing_unit"]
        )
        value["target_unit"] = DefensiveFireUnitSnapshot(
            **value["target_unit"]
        )
        return DefensiveFireEvent(**value)

    @staticmethod
    def _incompatible(category):
        raise SavedGameIncompatibleError(category)
