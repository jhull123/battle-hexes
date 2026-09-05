"""Read-only schemas for authoritative game-event history."""

from typing import Literal

from .api_model import ApiBaseModel


class ReinforcementEventModel(ApiBaseModel):
    outcome: Literal["arrived", "blocked"]
    unit_count: int
    entry_coordinate: tuple[int, int]


class CombatUnitModel(ApiBaseModel):
    name: str
    attack: int
    defense: int
    movement: int


class CombatTerrainModel(ApiBaseModel):
    name: str
    odds_shift: int


class CombatOutcomeModel(ApiBaseModel):
    code: str
    text: str
    summary: str


class CombatEventModel(ApiBaseModel):
    attackers: list[CombatUnitModel]
    defenders: list[CombatUnitModel]
    base_odds: tuple[int, int]
    modified_odds: tuple[int, int]
    defender_terrain: CombatTerrainModel
    die_roll: int
    result: CombatOutcomeModel
    eliminated_units: list[str]
    retreated_units: list[str]


class GameLogEventsModel(ApiBaseModel):
    reinforcements: list[ReinforcementEventModel]
    combat: list[CombatEventModel]


class GameLogRecordModel(ApiBaseModel):
    turn_number: int
    player_name: str
    events: GameLogEventsModel


def _record_for_event(records_by_key, event) -> GameLogRecordModel:
    key = (event.turn_number, event.player_name)
    if key not in records_by_key:
        records_by_key[key] = GameLogRecordModel(
            turn_number=event.turn_number,
            player_name=event.player_name,
            events=GameLogEventsModel(reinforcements=[], combat=[]),
        )
    return records_by_key[key]


def _combat_event_model(event) -> CombatEventModel:
    return CombatEventModel(
        attackers=[CombatUnitModel(**vars(unit)) for unit in event.attackers],
        defenders=[CombatUnitModel(**vars(unit)) for unit in event.defenders],
        base_odds=event.base_odds,
        modified_odds=event.modified_odds,
        defender_terrain=CombatTerrainModel(**vars(event.defender_terrain)),
        die_roll=event.die_roll,
        result=CombatOutcomeModel(**vars(event.result)),
        eliminated_units=list(event.eliminated_units),
        retreated_units=list(event.retreated_units),
    )


def game_log_from_game(game) -> list[GameLogRecordModel]:
    """Group already-recorded core events, returning newest entries first."""
    records_by_key: dict[tuple[int, str], GameLogRecordModel] = {}
    for event in reversed(game.reinforcements_deployer.game_log):
        record = _record_for_event(records_by_key, event)
        reinforcement = ReinforcementEventModel(
            outcome=event.outcome,
            unit_count=event.unit_count,
            entry_coordinate=event.entry_coordinate,
        )
        record.events.reinforcements.append(reinforcement)
    for event in reversed(getattr(game, "combat_log", [])):
        record = _record_for_event(records_by_key, event)
        record.events.combat.append(_combat_event_model(event))
    return sorted(
        records_by_key.values(),
        key=lambda record: record.turn_number,
        reverse=True,
    )
