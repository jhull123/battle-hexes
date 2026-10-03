from botocore.exceptions import EndpointConnectionError
import pytest

from battle_hexes_api.persistence import (
    EncodedItemBudget,
    GameNotFoundError,
    GameRepositoryDynamoDB,
    GameRepositoryInMemory,
    InMemoryItemSizer,
    InstrumentedGameRepository,
    PersistenceUnavailableError,
)
from battle_hexes_api.persistence.dynamodb_codec import (
    encode_game,
    encode_receipt,
)
from battle_hexes_api.persistence.in_memory import _game_item, _receipt_item
from tests.test_game_repository_contract import (
    ControlledClock,
    make_game,
    make_receipt,
)


class Sink:
    def __init__(self, error=None):
        self.events = []
        self.error = error

    def emit(self, event):
        if self.error:
            raise self.error
        self.events.append(event)


def instrument(repository, sink, timer=lambda: 1.0, dynamodb=False):
    return InstrumentedGameRepository(
        repository,
        "dynamodb" if dynamodb else "in_memory",
        repository._item_sizer,
        encode_game if dynamodb else _game_item,
        encode_receipt if dynamodb else _receipt_item,
        sink=sink,
        timer=timer,
    )


def test_emits_bounded_outcomes_sizes_and_no_identifiers():
    sink = Sink()
    repository = GameRepositoryInMemory(
        ControlledClock(), InMemoryItemSizer(), EncodedItemBudget()
    )
    observed = instrument(repository, sink)

    observed.create_game(make_game(), make_receipt())
    observed.find_receipt("a" * 64)
    with pytest.raises(GameNotFoundError):
        observed.load_game("missing-secret-id")

    assert [event.outcome for event in sink.events] == [
        "success", "replay", "not_found_expired"
    ]
    created = sink.events[0].fields()
    assert created["game_version"] == 1
    assert created["game_item_bytes"] > 0
    assert created["receipt_item_bytes"] > 0
    serialized = repr([event.fields() for event in sink.events])
    assert "a" * 64 not in serialized
    assert "missing-secret-id" not in serialized


def test_sink_failure_does_not_change_committed_result():
    repository = GameRepositoryInMemory(
        ControlledClock(), InMemoryItemSizer(), EncodedItemBudget()
    )
    observed = instrument(repository, Sink(RuntimeError("metrics down")))

    assert observed.create_game(make_game(), make_receipt()) == make_receipt()
    assert repository.load_game("game-1") == make_game()


class FailingClient:
    def get_item(self, **_request):
        raise EndpointConnectionError(endpoint_url="https://secret.invalid")


def test_dynamodb_error_uses_safe_bounded_category():
    repository = GameRepositoryDynamoDB(
        "games", FailingClient(), ControlledClock(), InMemoryItemSizer(),
        EncodedItemBudget(),
    )
    sink = Sink()

    with pytest.raises(PersistenceUnavailableError):
        instrument(repository, sink, dynamodb=True).load_game("game-1")

    assert sink.events[0].outcome == "persistence_unavailable"
    assert sink.events[0].dynamodb_error_category == "endpoint_network"
    assert "secret.invalid" not in repr(sink.events[0].fields())
