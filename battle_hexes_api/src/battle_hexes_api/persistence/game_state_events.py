"""Conversion between JSON history values and core event dataclasses."""

import math
from collections.abc import Collection, Mapping
from typing import Any

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


def decode_reinforcement_event(
    value: Mapping[str, Any],
) -> ReinforcementArrivalEvent:
    value = dict(value)
    value["entry_coordinate"] = tuple(value["entry_coordinate"])
    return ReinforcementArrivalEvent(**value)


def decode_combat_event(value: Mapping[str, Any]) -> CombatEvent:
    value = dict(value)
    value["attackers"] = tuple(
        CombatUnitSnapshot(**item) for item in value["attackers"]
    )
    value["defenders"] = tuple(
        CombatUnitSnapshot(**item) for item in value["defenders"]
    )
    value["base_odds"] = tuple(value["base_odds"])
    value["modified_odds"] = tuple(value["modified_odds"])
    value["defender_terrain"] = CombatTerrainSnapshot(
        **value["defender_terrain"]
    )
    value["result"] = CombatOutcomeSnapshot(**value["result"])
    value["eliminated_units"] = tuple(value["eliminated_units"])
    value["retreated_units"] = tuple(value["retreated_units"])
    return CombatEvent(**value)


def decode_defensive_fire_event(
    value: Mapping[str, Any],
) -> DefensiveFireEvent:
    value = dict(value)
    value["firing_unit"] = DefensiveFireUnitSnapshot(**value["firing_unit"])
    value["target_unit"] = DefensiveFireUnitSnapshot(**value["target_unit"])
    return DefensiveFireEvent(**value)


def validate_histories(
    reinforcement_history: list[dict[str, Any]],
    combat_history: list[dict[str, Any]],
    defensive_fire_history: list[dict[str, Any]],
    *,
    player_names: Collection[str],
    unit_ids: Collection[str],
) -> None:
    try:
        for value in reinforcement_history:
            event = decode_reinforcement_event(value)
            if event.player_name not in player_names:
                raise ValueError
            if len(event.entry_coordinate) != 2:
                raise ValueError

        for value in combat_history:
            event = decode_combat_event(value)
            participant_names = {
                item.name for item in event.attackers + event.defenders
            }
            if (
                event.player_name not in player_names
                or any(
                    not isinstance(item.name, str) for item in event.attackers
                )
                or any(
                    not isinstance(item.name, str) for item in event.defenders
                )
                or any(
                    item not in participant_names
                    for item in event.eliminated_units
                )
                or any(
                    item not in participant_names
                    for item in event.retreated_units
                )
            ):
                raise ValueError

        for value in defensive_fire_history:
            event = decode_defensive_fire_event(value)
            if (
                event.player_name not in player_names
                or event.firing_unit.unit_id not in unit_ids
                or event.target_unit.unit_id not in unit_ids
                or not math.isfinite(event.success_probability)
                or not math.isfinite(event.random_roll)
            ):
                raise ValueError
    except (TypeError, ValueError, KeyError) as error:
        raise ValueError("invalid history") from error
