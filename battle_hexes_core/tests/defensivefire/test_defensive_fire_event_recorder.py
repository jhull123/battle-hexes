from types import SimpleNamespace

from battle_hexes_core.defensivefire.defensive_fire_event_recorder import (
    DefensiveFireEventRecorder,
)


class UnitStub:
    def __init__(self, unit_id, name):
        self.unit_id = unit_id
        self.name = name

    def get_id(self):
        return self.unit_id

    def get_name(self):
        return self.name


class BoardStub:
    def __init__(self, units):
        self.units = units

    def get_units(self):
        return self.units


def result(firing_unit_id, outcome, destination, probability, roll):
    return SimpleNamespace(
        firing_unit_id=firing_unit_id,
        target_unit_id="target",
        outcome=outcome,
        retreat_destination=destination,
        probability=probability,
        roll=roll,
    )


def test_records_normalized_events_in_resolver_order():
    target = UnitStub("target", "Target")
    board = BoardStub([
        UnitStub("firing-a", "Firing A"),
        UnitStub("firing-b", "Firing B"),
        UnitStub("firing-c", "Firing C"),
    ])
    game_log = []
    recorder = DefensiveFireEventRecorder(board, game_log)

    recorder.record([
        result("firing-a", "no_effect", None, 0.25, 0.75),
        result("firing-b", "retreat", (2, 3), 0.5, 0.1),
        result("firing-c", "retreat", None, 0.6, 0.2),
    ], target, 4, "Moving Player")

    assert [event.firing_unit.unit_id for event in game_log] == [
        "firing-a", "firing-b", "firing-c",
    ]
    assert [event.outcome for event in game_log] == [
        "noEffect", "retreated", "eliminated",
    ]
    assert game_log[0].target_unit.name == "Target"
    assert game_log[0].success_probability == 0.25
    assert game_log[0].random_roll == 0.75
    assert game_log[0].player_name == "Moving Player"
    assert game_log[0].turn_number == 4
    assert game_log[1].summary == "Firing B forced Target to retreat."
    assert game_log[2].summary == "Firing C eliminated Target."
