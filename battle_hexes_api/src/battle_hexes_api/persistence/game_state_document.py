"""Validated persistence-document models for authoritative game state."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Player(Model):
    name: str
    type_id: Literal["human", "random", "q-learning"]


class PendingCombat(Model):
    attacker_unit_ids: list[str]
    defender_unit_ids: list[str]


class Status(Model):
    state: Literal["in_progress", "completed"]
    winner_player_name: str | None
    winner_faction_id: str | None
    reason: str | None
    message: str | None


class Score(Model):
    player_name: str
    points: StrictInt


class Unit(Model):
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


class Reinforcement(Model):
    group_id: str
    entered: StrictBool


class Document(Model):
    state_schema_version: StrictInt
    game_id: str
    scenario_id: str
    scenario_version: str
    players: list[Player]
    current_player_name: str | None
    turn_number: StrictInt
    current_phase: Literal["movement", "combat", "end_turn"] | None
    pending_combats: list[PendingCombat]
    terminal: StrictBool
    game_status: Status
    scores: list[Score]
    active_unit_ids: list[str]
    units: list[Unit]
    reinforcements: list[Reinforcement]
    reinforcement_history: list[dict[str, Any]]
    combat_history: list[dict[str, Any]]
    defensive_fire_history: list[dict[str, Any]]
