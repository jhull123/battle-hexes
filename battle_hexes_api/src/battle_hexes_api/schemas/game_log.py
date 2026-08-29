"""Read-only schemas for authoritative reinforcement history."""

from typing import Literal

from .api_model import ApiBaseModel


class ReinforcementEventModel(ApiBaseModel):
    outcome: Literal["arrived", "blocked"]
    unit_count: int
    entry_coordinate: tuple[int, int]


class GameLogEventsModel(ApiBaseModel):
    reinforcements: list[ReinforcementEventModel]


class GameLogRecordModel(ApiBaseModel):
    turn_number: int
    player_name: str
    events: GameLogEventsModel


def game_log_from_game(game) -> list[GameLogRecordModel]:
    """Group already-recorded core events, returning newest entries first."""
    records_by_key = {}
    for event in reversed(game.reinforcements_deployer.game_log):
        key = (event.turn_number, event.player_name)
        if key not in records_by_key:
            records_by_key[key] = GameLogRecordModel(
                turn_number=event.turn_number,
                player_name=event.player_name,
                events=GameLogEventsModel(reinforcements=[]),
            )
        reinforcement = ReinforcementEventModel(
            outcome=event.outcome,
            unit_count=event.unit_count,
            entry_coordinate=event.entry_coordinate,
        )
        records_by_key[key].events.reinforcements.append(reinforcement)
    return list(records_by_key.values())
