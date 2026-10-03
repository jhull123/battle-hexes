import json
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from battle_hexes_api.command_adapters import (
    CombatAdapter,
    CombatResponseSerializer,
    CreateGameAdapter,
    EndMovementAdapter,
    EndTurnAdapter,
    GameAlreadyCompletedError,
    HumanMoveAdapter,
    MovementAdapter,
    MovementCommandResult,
    MovementResponseSerializer,
)
from battle_hexes_core.defensivefire.defensive_fire import (
    MovementResolutionResult,
)


def command_game(state="in_progress"):
    game = MagicMock()
    game.get_game_status.return_value = SimpleNamespace(state=state)
    game.is_game_over.return_value = False
    return game


@pytest.mark.parametrize(
    "adapter",
    [
        MovementAdapter(),
        HumanMoveAdapter(MagicMock()),
        EndMovementAdapter(MagicMock()),
        CombatAdapter(MagicMock()),
        EndTurnAdapter(MagicMock()),
    ],
)
def test_existing_adapters_reject_completed_game_before_mutation(adapter):
    game = command_game("completed")

    with pytest.raises(GameAlreadyCompletedError):
        adapter(game)

    assert game.mock_calls == [
        call.get_game_status(),
    ]


def test_creation_returns_scenario_metadata_after_creating_game():
    calls = []
    request = SimpleNamespace(scenario_id="scenario", player_types=["a", "b"])
    scenario = SimpleNamespace(version="7")
    created_game = object()
    creator = MagicMock()
    creator.create_sample_game.side_effect = (
        lambda *args: calls.append(("create", args)) or created_game
    )

    result = CreateGameAdapter(
        request,
        scenario_loader=lambda value: calls.append(("scenario", value))
        or scenario,
        game_creator=creator,
    )()

    assert calls == [
        ("scenario", "scenario"),
        ("create", ("scenario", ["a", "b"])),
    ]
    assert result.game is created_game
    assert result.scenario_id == "scenario"
    assert result.scenario_version == "7"


def test_movement_retains_results_and_runs_completion_callbacks_last():
    events = []
    player = MagicMock()
    player.movement.side_effect = lambda: events.append("plans") or ["plan"]
    player.end_game_cb.side_effect = lambda: events.append("callback")
    game = command_game()
    game.get_current_player.return_value = player
    resolution = object()
    game.apply_movement_plans.side_effect = (
        lambda plans: events.append(("apply", plans)) or resolution
    )
    game.is_game_over.return_value = True
    game.get_players.return_value = [player]

    result = MovementAdapter()(game)

    assert result == MovementCommandResult(("plan",), resolution)
    assert events == ["plans", ("apply", ("plan",)), "callback"]


def test_end_movement_preserves_workflow_order():
    events = []
    sparse_board = MagicMock()
    sparse_board.to_movement_plans.side_effect = (
        lambda board: events.append("convert") or []
    )
    scorer = MagicMock()
    scorer.award_hold_objectives.side_effect = lambda game: events.append(
        "score"
    )
    game = command_game()
    game.apply_movement_plans.side_effect = (
        lambda plans: events.append("apply") or object()
    )
    game.end_movement.side_effect = lambda: events.append("end")

    EndMovementAdapter(sparse_board, lambda: scorer)(game)

    assert events == ["convert", "apply", "score", "end"]


def test_combat_resolves_once_and_scores_before_callbacks():
    events = []
    sparse_board = MagicMock()
    sparse_board.apply_to_board.side_effect = lambda board: events.append(
        "board"
    )
    combat = MagicMock()
    results = object()
    combat.resolve_combat.side_effect = (
        lambda: events.append("combat") or results
    )
    scorer = MagicMock()
    scorer.award_hold_objectives_after_combat.side_effect = (
        lambda game, value: events.append("score")
    )
    scorer.recalculate_scenario_victory.side_effect = (
        lambda game: events.append("victory")
    )
    player = MagicMock()
    player.end_game_cb.side_effect = lambda: events.append("callback")
    game = command_game()
    game.end_combat.side_effect = lambda: events.append("end")
    game.is_game_over.return_value = True
    game.get_players.return_value = [player]

    result = CombatAdapter(
        sparse_board,
        combat_factory=lambda game: combat,
        scorer_factory=lambda: scorer,
    )(game)

    assert result.combat_results is results
    assert events == [
        "board", "combat", "end", "score", "victory", "callback"
    ]


def test_end_turn_synchronizes_scores_and_transitions_in_order():
    events = []
    sparse_board = MagicMock()
    sparse_board.apply_to_board.side_effect = lambda board: events.append(
        "board"
    )
    scorer = MagicMock()
    scorer.recalculate_scenario_victory.side_effect = (
        lambda game: events.append("victory")
    )
    game = command_game()
    game.end_turn.side_effect = lambda: events.append("turn")

    assert EndTurnAdapter(sparse_board, lambda: scorer)(game) is None
    assert events == ["board", "victory", "turn"]


def test_movement_serializer_sets_consistent_versions(sample_game):
    result = MovementCommandResult((), MovementResolutionResult())

    status, body, content_type, headers = MovementResponseSerializer("3")(
        sample_game, result, 8
    )
    payload = json.loads(body)

    assert status == 200
    assert content_type == "application/json"
    assert headers == {}
    assert payload["gameVersion"] == 8
    assert payload["game"]["gameVersion"] == 8
    assert payload["game"]["scenarioVersion"] == "3"
    assert payload["sparseBoard"]["gameVersion"] == 8


def test_combat_serializer_emits_supplied_version(sample_game):
    results = MagicMock()
    results.get_battles.return_value = []
    result = SimpleNamespace(combat_results=results)

    _, body, _, _ = CombatResponseSerializer()(sample_game, result, 5)

    assert json.loads(body)["gameVersion"] == 5


@pytest.fixture
def sample_game():
    from battle_hexes_api.gamecreator import GameCreator

    return GameCreator.create_sample_game("elim_1", ["human", "random"])
