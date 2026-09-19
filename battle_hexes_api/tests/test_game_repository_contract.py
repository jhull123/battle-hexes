"""Adapter-neutral behavioral contract for game repositories."""

from threading import Barrier, Thread

import pytest

from battle_hexes_api.persistence import (
    CommandIdentity,
    CommandReceipt,
    EncodedItemBudget,
    GameAlreadyExistsError,
    GameNotFoundError,
    GameRepositoryInMemory,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceCapacityError,
    StoredGame,
)


class ControlledClock:
    def __init__(self, now=100):
        self.current = now

    def now(self):
        return self.current


class ControlledSizer:
    def __init__(self):
        self.sizes = {"game": 1, "command_receipt": 1}
        self.items = []

    def size_bytes(self, item):
        self.items.append(item)
        return self.sizes[item["item_type"]]


@pytest.fixture
def repository_context():
    clock = ControlledClock()
    sizer = ControlledSizer()
    repository = GameRepositoryInMemory(
        clock, sizer, EncodedItemBudget()
    )
    return repository, clock, sizer


def make_game(version=1, expires_at=200, state=b"{}"):
    return StoredGame(
        "game-1", version, 1, "scenario-1", "1", state,
        100, expires_at,
    )


def make_receipt(
    version=1,
    key="a" * 64,
    fingerprint="b" * 64,
    expires_at=200,
    headers=None,
):
    return CommandReceipt(
        CommandIdentity(key, fingerprint),
        "game-1",
        version,
        200,
        "application/json",
        b"{}",
        headers or {"Game-Version": str(version)},
        100,
        expires_at,
    )


def test_create_load_and_lookup_are_detached(repository_context):
    repository, _, _ = repository_context
    headers = {"Game-Version": "1"}
    receipt = make_receipt(headers=headers)
    result = repository.create_game(make_game(state=b'{"turn":1}'), receipt)
    headers["Game-Version"] = "changed"

    first = repository.load_game("game-1")
    second = repository.load_game("game-1")
    stored_receipt = repository.find_receipt("a" * 64)
    assert first == second == make_game(state=b'{"turn":1}')
    assert first is not second
    assert result == stored_receipt
    assert result is not stored_receipt
    assert stored_receipt.response_headers == {"Game-Version": "1"}


def test_create_and_commit_enforce_game_preconditions(repository_context):
    repository, _, _ = repository_context
    repository.create_game(make_game(), make_receipt())
    with pytest.raises(GameAlreadyExistsError):
        repository.create_game(
            make_game(), make_receipt(key="c" * 64)
        )
    with pytest.raises(GameVersionConflictError):
        repository.commit_command(
            2, make_game(version=3), make_receipt(3, key="d" * 64)
        )
    repository.commit_command(
        1, make_game(version=2), make_receipt(2, key="e" * 64)
    )
    assert repository.load_game("game-1").version == 2


def test_expiry_is_inclusive_and_physical_keys_are_reusable(
    repository_context,
):
    repository, clock, _ = repository_context
    repository.create_game(make_game(), make_receipt())
    clock.current = 200
    with pytest.raises(GameNotFoundError):
        repository.load_game("game-1")
    assert repository.find_receipt("a" * 64) is None
    replacement = make_receipt(expires_at=300)
    repository.create_game(
        make_game(expires_at=300), replacement
    )
    assert repository.load_game("game-1").expires_at == 300


def test_receipt_replay_precedes_game_and_capacity_checks(
    repository_context,
):
    repository, clock, sizer = repository_context
    original = repository.create_game(
        make_game(), make_receipt(expires_at=300)
    )
    clock.current = 200
    sizer.sizes["game"] = 999999
    replay = repository.commit_command(
        8, make_game(version=9, expires_at=300),
        make_receipt(version=9, expires_at=300),
    )
    assert replay == original

    conflicting = make_receipt(version=9, fingerprint="c" * 64)
    with pytest.raises(IdempotencyConflictError):
        repository.commit_command(
            8, make_game(version=9, expires_at=300), conflicting
        )


@pytest.mark.parametrize("oversized_kind", ["game", "command_receipt"])
def test_capacity_failure_rolls_back(repository_context, oversized_kind):
    repository, _, sizer = repository_context
    repository.create_game(make_game(), make_receipt())
    sizer.sizes[oversized_kind] = 358401
    with pytest.raises(PersistenceCapacityError):
        repository.commit_command(
            1, make_game(version=2),
            make_receipt(version=2, key="c" * 64),
        )
    assert repository.load_game("game-1").version == 1
    assert repository.find_receipt("c" * 64) is None


def test_two_writers_publish_one_transition(repository_context):
    repository, _, _ = repository_context
    repository.create_game(make_game(), make_receipt())
    barrier = Barrier(3)
    outcomes = []

    def commit(key):
        barrier.wait()
        try:
            outcomes.append(repository.commit_command(
                1, make_game(version=2), make_receipt(2, key=key)
            ))
        except GameVersionConflictError as error:
            outcomes.append(error)

    threads = [
        Thread(target=commit, args=("c" * 64,)),
        Thread(target=commit, args=("d" * 64,)),
    ]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()

    assert sum(isinstance(value, CommandReceipt) for value in outcomes) == 1
    assert sum(
        isinstance(value, GameVersionConflictError) for value in outcomes
    ) == 1
    assert repository.load_game("game-1").version == 2
