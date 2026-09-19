"""Semantic validation for persistence documents against a scenario."""

from dataclasses import dataclass
import math

from battle_hexes_core.scenario.scenario_loader import ScenarioData

from .errors import SavedGameIncompatibleError
from .game_state_document import Document
from .game_state_events import validate_histories


@dataclass(frozen=True)
class ValidationContext:
    player_names: tuple[str, ...]
    unit_ids: tuple[str, ...]
    active_unit_ids: frozenset[str]
    owner_by_unit: dict[str, str]
    current_player_name: str | None


class GameStateValidator:
    def __init__(self, schema_version: int) -> None:
        self._schema_version = schema_version

    def validate(self, document: Document, scenario: ScenarioData) -> None:
        self._validate_metadata(document, scenario)
        context = self._validate_structure(document, scenario)
        self._validate_units(document, scenario, context)
        self._validate_runtime(document, context)
        self._validate_pending_combats(document, context)
        try:
            validate_histories(
                document.reinforcement_history,
                document.combat_history,
                document.defensive_fire_history,
                player_names=context.player_names,
                unit_ids=context.unit_ids,
            )
        except ValueError as error:
            self._incompatible("history", error)

    def _validate_metadata(self, document, scenario):
        if (
            document.state_schema_version != self._schema_version
            or not document.game_id
            or document.scenario_id != scenario.id
        ):
            self._incompatible("metadata")

    def _validate_structure(self, document, scenario):
        expected_players = []
        for faction in scenario.factions:
            if faction.player not in expected_players:
                expected_players.append(faction.player)
        player_names = tuple(player.name for player in document.players)
        if player_names != tuple(expected_players) or len(player_names) != len(
            set(player_names)
        ):
            self._incompatible("players")

        unit_ids = tuple(unit.id for unit in scenario.units)
        saved_unit_ids = tuple(unit.unit_id for unit in document.units)
        if saved_unit_ids != unit_ids or len(saved_unit_ids) != len(
            set(saved_unit_ids)
        ):
            self._incompatible("units")

        expected_groups = tuple(
            group.id for group in (scenario.reinforcements or [])
        )
        saved_groups = tuple(
            group.group_id for group in document.reinforcements
        )
        if saved_groups != expected_groups:
            self._incompatible("reinforcements")

        active_unit_ids = frozenset(
            unit.unit_id
            for unit in document.units
            if unit.disposition == "active"
        )
        if (
            set(document.active_unit_ids) != active_unit_ids
            or len(document.active_unit_ids)
            != len(set(document.active_unit_ids))
        ):
            self._incompatible("active_units")

        owner_by_unit = {
            unit.id: next(
                faction.player
                for faction in scenario.factions
                if faction.id == unit.faction
            )
            for unit in scenario.units
        }
        return ValidationContext(
            player_names=player_names,
            unit_ids=unit_ids,
            active_unit_ids=active_unit_ids,
            owner_by_unit=owner_by_unit,
            current_player_name=document.current_player_name,
        )

    def _validate_units(self, document, scenario, context):
        pending_scenario_ids = {
            unit_id
            for group, state in zip(
                scenario.reinforcements or [], document.reinforcements
            )
            if not state.entered
            for unit_id in group.units
        }
        for unit in document.units:
            coordinates_present = (
                unit.row is not None and unit.column is not None
            )
            in_bounds = coordinates_present and (
                0 <= unit.row < scenario.board_size[0]
                and 0 <= unit.column < scenario.board_size[1]
            )
            if unit.disposition == "active" and not in_bounds:
                self._incompatible("coordinates")
            if unit.disposition != "active" and coordinates_present:
                self._incompatible("coordinates")
            if (unit.disposition == "reinforcement") != (
                unit.unit_id in pending_scenario_ids
            ):
                self._incompatible("disposition")
            if not math.isfinite(unit.defensive_fire_modifier):
                self._incompatible("numeric_value")

    def _validate_runtime(self, document, context):
        if [score.player_name for score in document.scores] != list(
            context.player_names
        ) or any(score.points < 0 for score in document.scores):
            self._incompatible("scores")
        if document.turn_number < 1:
            self._incompatible("turn_number")
        if document.terminal:
            valid = (
                document.current_player_name is None
                and document.current_phase is None
                and not document.pending_combats
                and document.game_status.state == "completed"
            )
        else:
            valid = (
                document.current_player_name in context.player_names
                and document.current_phase is not None
                and document.game_status.state == "in_progress"
            )
        if not valid:
            self._incompatible("terminal_state")

    def _validate_pending_combats(self, document, context):
        current_player = context.current_player_name
        for combat in document.pending_combats:
            attackers = combat.attacker_unit_ids
            defenders = combat.defender_unit_ids
            invalid = (
                not attackers
                or not defenders
                or len(set(attackers)) != len(attackers)
                or len(set(defenders)) != len(defenders)
                or set(attackers) & set(defenders)
                or not set(attackers + defenders) <= context.active_unit_ids
                or current_player is None
                or any(
                    context.owner_by_unit[unit_id] != current_player
                    for unit_id in attackers
                )
                or any(
                    context.owner_by_unit[unit_id] == current_player
                    for unit_id in defenders
                )
            )
            if invalid:
                self._incompatible("pending_combats")

    @staticmethod
    def _incompatible(category, cause=None):
        raise SavedGameIncompatibleError(category) from cause
