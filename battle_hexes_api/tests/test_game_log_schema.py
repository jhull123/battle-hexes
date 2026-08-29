"""Tests for reinforcement game-log serialization."""

from types import SimpleNamespace

from battle_hexes_api.schemas.game_log import game_log_from_game
from battle_hexes_core.game.reinforcement import ReinforcementArrivalEvent


def test_game_log_is_grouped_and_serialized_newest_first():
    events = [
        ReinforcementArrivalEvent(3, "Player 1", 2, (0, 0), "blocked"),
        ReinforcementArrivalEvent(3, "Player 2", 1, (0, 16), "arrived"),
        ReinforcementArrivalEvent(4, "Player 1", 2, (0, 0), "arrived"),
    ]
    game = SimpleNamespace(
        reinforcements_deployer=SimpleNamespace(game_log=events),
    )

    payload = [
        record.model_dump(by_alias=True)
        for record in game_log_from_game(game)
    ]

    assert payload == [
        {
            "turnNumber": 4,
            "playerName": "Player 1",
            "events": {"reinforcements": [{
                "outcome": "arrived",
                "unitCount": 2,
                "entryCoordinate": (0, 0),
            }]},
        },
        {
            "turnNumber": 3,
            "playerName": "Player 2",
            "events": {"reinforcements": [{
                "outcome": "arrived",
                "unitCount": 1,
                "entryCoordinate": (0, 16),
            }]},
        },
        {
            "turnNumber": 3,
            "playerName": "Player 1",
            "events": {"reinforcements": [{
                "outcome": "blocked",
                "unitCount": 2,
                "entryCoordinate": (0, 0),
            }]},
        },
    ]
