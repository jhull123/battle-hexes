import logging
import random
from typing import Any

from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireResult,
    DefensiveFireSettings,
)


class DefensiveFireResolver:
    def __init__(self, board, settings: Any = None):
        self.board = board
        self.logger = logging.getLogger(__name__)
        self.settings = self._coerce_settings(settings)

    def set_settings(self, settings: Any = None) -> None:
        self.settings = self._coerce_settings(settings)

    def _coerce_settings(self, settings: Any) -> DefensiveFireSettings:
        if settings is None:
            return DefensiveFireSettings()
        if isinstance(settings, DefensiveFireSettings):
            return settings
        return DefensiveFireSettings(
            base_probability=settings.base_probability,
            minimum=settings.minimum,
            maximum=settings.maximum,
        )

    def resolve_defensive_fire(
        self,
        mover,
        trigger_hex,
        current_player,
    ) -> list[DefensiveFireResult]:
        if mover.get_coords() is None:
            return []

        results: list[DefensiveFireResult] = []
        for defender in self._eligible_defenders(mover, current_player):
            if self._mover_left_trigger_hex(mover, trigger_hex):
                break
            results.append(
                self._resolve_single_defender(
                    defender,
                    mover,
                    trigger_hex,
                    current_player,
                )
            )
        return results

    def _eligible_defenders(self, mover, current_player) -> list:
        return sorted(
            [
                unit
                for unit in self.board.get_units()
                if self._is_eligible_defender(unit, mover, current_player)
            ],
            key=lambda unit: str(unit.get_id()),
        )

    def _is_eligible_defender(self, unit, mover, current_player) -> bool:
        return (
            unit.get_coords() is not None
            and not current_player.owns(unit)
            and unit.is_adjacent(mover)
            and unit.has_defensive_fire(current_player)
        )

    def _mover_left_trigger_hex(self, mover, trigger_hex) -> bool:
        return mover.get_coords() != (trigger_hex.row, trigger_hex.column)

    def _resolve_single_defender(
        self,
        defender,
        mover,
        trigger_hex,
        current_player,
    ) -> DefensiveFireResult:
        target_before = mover.get_coords()
        components = self._probability_components(defender, trigger_hex)
        probability = self._clamp_probability(
            components["unclamped_probability"]
        )
        roll = random.random()
        defender.spend_defensive_fire(current_player)
        outcome, retreat_destination = self._resolve_outcome(
            defender,
            mover,
            current_player,
            probability,
            roll,
        )
        result = DefensiveFireResult(
            firing_unit_id=str(defender.get_id()),
            target_unit_id=str(mover.get_id()),
            trigger_hex=(trigger_hex.row, trigger_hex.column),
            target_hex_before=target_before,
            outcome=outcome,
            retreat_destination=retreat_destination,
            probability=probability,
            roll=roll,
        )
        self._log_resolution(result, components)
        return result

    def _probability_components(
        self,
        firing_unit,
        target_hex,
    ) -> dict[str, float]:
        terrain = target_hex.terrain
        return {
            "base_probability": self.settings.base_probability,
            "unit_modifier": getattr(
                firing_unit,
                "defensive_fire_modifier",
                1.0,
            ),
            "terrain_modifier": (
                terrain.defensive_fire_modifier if terrain is not None else 1.0
            ),
            "minimum": self.settings.minimum,
            "maximum": self.settings.maximum,
            "unclamped_probability": (
                self.settings.base_probability
                * getattr(firing_unit, "defensive_fire_modifier", 1.0)
                * (
                    terrain.defensive_fire_modifier
                    if terrain is not None
                    else 1.0
                )
            ),
        }

    def _clamp_probability(self, probability: float) -> float:
        return min(
            self.settings.maximum,
            max(self.settings.minimum, probability),
        )

    def _log_resolution(
        self,
        result: DefensiveFireResult,
        components: dict[str, float],
    ) -> None:
        self.logger.info(
            "defensive_fire: firing_unit=%s target_unit=%s outcome=%s "
            "trigger_hex=%s target_before=%s roll=%.6f calc="
            "%.6f(base)*%.6f(unit)*%.6f(terrain)=%.6f unclamped, "
            "clamped[min=%.6f,max=%.6f]=%.6f retreat_destination=%s",
            result.firing_unit_id,
            result.target_unit_id,
            result.outcome,
            result.trigger_hex,
            result.target_hex_before,
            result.roll,
            components["base_probability"],
            components["unit_modifier"],
            components["terrain_modifier"],
            components["unclamped_probability"],
            components["minimum"],
            components["maximum"],
            result.probability,
            result.retreat_destination,
        )

    def _resolve_outcome(
        self,
        defender,
        mover,
        current_player,
        probability: float,
        roll: float,
    ) -> tuple[str, tuple[int, int] | None]:
        if roll >= probability:
            return "no_effect", None
        return self._apply_retreat(defender, mover, current_player)

    def _apply_retreat(
        self,
        defender,
        mover,
        current_player,
    ) -> tuple[str, tuple[int, int] | None]:
        defender_coords = defender.get_coords()
        mover.record_forced_retreat(current_player)
        if mover.forced_move(self.board, defender_coords, 1):
            return "retreat", mover.get_coords()
        self.board.remove_units([mover])
        return "retreat", None

    def defensive_fire_probability(self, firing_unit, target_hex) -> float:
        components = self._probability_components(firing_unit, target_hex)
        return self._clamp_probability(components["unclamped_probability"])
