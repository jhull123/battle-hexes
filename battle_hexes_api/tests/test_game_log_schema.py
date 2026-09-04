"""Tests for reinforcement game-log serialization."""

from types import SimpleNamespace

from battle_hexes_api.schemas.game_log import game_log_from_game
from battle_hexes_core.game.reinforcement import ReinforcementArrivalEvent
from battle_hexes_core.combat.combat_event import (
    CombatEvent,
    CombatOutcomeSnapshot,
    CombatTerrainSnapshot,
    CombatUnitSnapshot,
)


def test_game_log_is_grouped_and_serialized_newest_first():
    events = [
        ReinforcementArrivalEvent(3, "Player 1", 2, (0, 0), "blocked"),
        ReinforcementArrivalEvent(3, "Player 2", 1, (0, 16), "arrived"),
        ReinforcementArrivalEvent(4, "Player 1", 2, (0, 0), "arrived"),
    ]
    game = SimpleNamespace(
        reinforcements_deployer=SimpleNamespace(game_log=events),
        combat_log=[],
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
            }], "combat": []},
        },
        {
            "turnNumber": 3,
            "playerName": "Player 2",
            "events": {"reinforcements": [{
                "outcome": "arrived",
                "unitCount": 1,
                "entryCoordinate": (0, 16),
            }], "combat": []},
        },
        {
            "turnNumber": 3,
            "playerName": "Player 1",
            "events": {"reinforcements": [{
                "outcome": "blocked",
                "unitCount": 2,
                "entryCoordinate": (0, 0),
            }], "combat": []},
        },
    ]


def test_combat_history_serializes_complete_camel_case_contract():
    event = CombatEvent(
        turn_number=3,
        player_name="Player 2",
        attackers=(CombatUnitSnapshot("Unit A", 4, 4, 2),),
        defenders=(CombatUnitSnapshot("Unit C", 3, 3, 3),),
        base_odds=(3, 1),
        modified_odds=(2, 1),
        defender_terrain=CombatTerrainSnapshot("Woods", -1),
        die_roll=4,
        result=CombatOutcomeSnapshot(
            "DEFENDER_RETREAT_2",
            "Defender Retreat 2 Hexes",
            "Unit C retreated 2 hexes.",
        ),
        eliminated_units=(),
        retreated_units=("Unit C",),
    )
    game = SimpleNamespace(
        reinforcements_deployer=SimpleNamespace(game_log=[]),
        combat_log=[event],
    )

    payload = game_log_from_game(game)[0].model_dump(by_alias=True)

    assert payload == {
        "turnNumber": 3,
        "playerName": "Player 2",
        "events": {
            "reinforcements": [],
            "combat": [{
                "attackers": [{
                    "name": "Unit A", "attack": 4,
                    "defense": 4, "movement": 2,
                }],
                "defenders": [{
                    "name": "Unit C", "attack": 3,
                    "defense": 3, "movement": 3,
                }],
                "baseOdds": (3, 1),
                "modifiedOdds": (2, 1),
                "defenderTerrain": {"name": "Woods", "oddsShift": -1},
                "dieRoll": 4,
                "result": {
                    "code": "DEFENDER_RETREAT_2",
                    "text": "Defender Retreat 2 Hexes",
                    "summary": "Unit C retreated 2 hexes.",
                },
                "eliminatedUnits": [],
                "retreatedUnits": ["Unit C"],
            }],
        },
    }
