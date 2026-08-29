"""Behavior tests for fixed reinforcement arrival."""

from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.gamecreator.gamecreator import GameCreator
from battle_hexes_core.scenario.scenario import (
    Scenario,
    ScenarioEntryLocation,
    ScenarioFaction,
    ScenarioHexData,
    ScenarioReinforcement,
    ScenarioUnit,
)


def _game(arrival_turn=2, stacking_limit=2, group_units=("reserve1",)):
    players = [
        Player("Player 1", PlayerType.HUMAN, []),
        Player("Player 2", PlayerType.CPU, []),
    ]
    scenario = Scenario(
        id="fixed-reserves",
        name="Fixed reserves",
        board_size=(3, 3),
        stacking_limit=stacking_limit,
        factions=(
            ScenarioFaction("f1", "One", "#111", "Player 1"),
            ScenarioFaction("f2", "Two", "#222", "Player 2"),
        ),
        units=(
            ScenarioUnit("onboard1", "Onboard 1", "f1", "Infantry", 1, 1, 2),
            ScenarioUnit("onboard2", "Onboard 2", "f2", "Infantry", 1, 1, 2),
            ScenarioUnit("reserve1", "Reserve 1", "f2", "Infantry", 2, 3, 4,
                         defensive_fire_modifier=0.5),
            ScenarioUnit("reserve2", "Reserve 2", "f2", "Infantry", 2, 3, 4),
        ),
        hex_data=(
            ScenarioHexData((0, 0), units=("onboard1",)),
            ScenarioHexData((2, 2), units=("onboard2",)),
        ),
        reinforcements=(
            ScenarioReinforcement(
                "reserves",
                group_units,
                arrival_turn,
                ScenarioEntryLocation("fixed", (1, 1)),
            ),
        ),
    )
    return GameCreator().create_game(scenario, *players), players


def _advance_to_turn_two(game):
    game.next_player()
    game.next_player()


def test_group_enters_together_at_start_of_arrival_turn():
    game, _ = _game(group_units=("reserve1", "reserve2"))
    assert {unit.id for unit in game.board.get_units()} == {
        "onboard1", "onboard2"
    }

    _advance_to_turn_two(game)

    reserves = [unit for unit in game.board.get_units_at(1, 1)]
    assert [unit.id for unit in reserves] == ["reserve1", "reserve2"]
    assert all(unit.current_turn_movement_points_remaining == 4
               for unit in reserves)
    assert all(not unit.has_defensive_fire(game.current_player)
               for unit in reserves)


def test_blocked_group_stays_atomic_and_retries_later():
    game, _ = _game(group_units=("reserve1", "reserve2"))
    blocker = game.board.get_unit_by_id("onboard1")
    blocker.set_coords(1, 1)

    _advance_to_turn_two(game)
    assert not game.reinforcements_deployer.groups[0].entered
    assert game.board.get_units_at(1, 1) == [blocker]

    blocker.set_coords(0, 0)
    game.next_player()
    game.next_player()
    assert [unit.id for unit in game.board.get_units_at(1, 1)] == [
        "reserve1", "reserve2"
    ]
    assert [event.outcome for event in game.reinforcements_deployer.game_log] \
        == ["blocked", "arrived"]
    first, second = game.reinforcements_deployer.game_log
    assert first.turn_number == 2
    assert first.player_name == "Player 2"
    assert first.unit_count == 2
    assert first.entry_coordinate == (1, 1)
    assert second.turn_number == 3


def test_blocked_group_records_every_retry_in_creation_order():
    game, _ = _game(group_units=("reserve1", "reserve2"))
    game.board.get_unit_by_id("onboard1").set_coords(1, 1)

    _advance_to_turn_two(game)
    game.next_player()
    game.next_player()

    assert [
        (event.turn_number, event.outcome)
        for event in game.reinforcements_deployer.game_log
    ] == [(2, "blocked"), (3, "blocked")]


def test_pending_query_reports_scheduled_delayed_and_entered_state():
    game, _ = _game(arrival_turn=2)
    pending = game.reinforcements_deployer.pending(game.turn_number)
    assert pending[0].status == "scheduled"
    assert pending[0].arrival_turn == 2
    assert pending[0].coords == (1, 1)

    blocker = game.board.get_unit_by_id("onboard1")
    blocker.set_coords(1, 1)
    _advance_to_turn_two(game)
    game.next_player()
    game.next_player()
    assert game.reinforcements_deployer.pending(3)[0].status == "delayed"

    blocker.set_coords(0, 0)
    game.reinforcements_deployer.deploy_due(3)
    assert game.reinforcements_deployer.pending(3) == ()


def test_pending_reinforcement_prevents_premature_elimination():
    game, players = _game()
    game.board.get_unit_by_id("onboard2").set_coords(None, None)

    status = game.update_game_status()

    assert status.state == "in_progress"
    assert game.reinforcements_deployer.has_eligible_pending(
        players[1], game.turn_number, game.turn_limit
    )


def test_reinforcement_after_turn_limit_never_prolongs_game():
    game, players = _game(arrival_turn=4)
    game.turn_limit = 3
    game.board.get_unit_by_id("onboard2").set_coords(None, None)

    status = game.update_game_status()

    assert status.state == "completed"
    assert not game.reinforcements_deployer.has_eligible_pending(
        players[1], game.turn_number, game.turn_limit
    )
