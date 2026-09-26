"""Unit coverage for the low-level DynamoDB repository adapter."""

from botocore.exceptions import ClientError, EndpointConnectionError
import pytest

from battle_hexes_api.persistence import (
    CommandIdentity,
    CommandReceipt,
    EncodedItemBudget,
    GameAlreadyExistsError,
    GameNotFoundError,
    GameRepositoryDynamoDB,
    GameVersionConflictError,
    IdempotencyConflictError,
    PersistenceCapacityError,
    PersistenceUnavailableError,
    StoredGame,
)


class Clock:
    def __init__(self, now=100):
        self.value = now

    def now(self):
        return self.value


class Sizer:
    def __init__(self, size=1):
        self.size = size
        self.items = []

    def size_bytes(self, item):
        self.items.append(item)
        return self.size


class Client:
    def __init__(self):
        self.items = {}
        self.gets = []
        self.transactions = []
        self.transaction_error = None

    def get_item(self, **request):
        self.gets.append(request)
        key = (request["Key"]["pk"]["S"], request["Key"]["sk"]["S"])
        item = self.items.get(key)
        return {} if item is None else {"Item": item}

    def transact_write_items(self, **request):
        self.transactions.append(request)
        if self.transaction_error is not None:
            raise self.transaction_error
        for operation in request["TransactItems"]:
            if "Put" in operation:
                item = operation["Put"]["Item"]
                key = (item["pk"]["S"], item["sk"]["S"])
                self.items[key] = item
            else:
                update = operation["Update"]
                key = (update["Key"]["pk"]["S"],
                       update["Key"]["sk"]["S"])
                current = dict(self.items[key])
                for name in update["ExpressionAttributeNames"].values():
                    current[name] = update["ExpressionAttributeValues"][
                        f":{name}"
                    ]
                self.items[key] = current
        return {}


def game(version=1, expires_at=200):
    return StoredGame(
        "game-1", version, 1, "scenario-1", "1", b"{}", 100,
        expires_at,
    )


def receipt(version=1, key="a" * 64, fingerprint="b" * 64,
            expires_at=200):
    return CommandReceipt(
        CommandIdentity(key, fingerprint), "game-1", version, 200,
        "application/json", b"{}", {"Game-Version": str(version)},
        100, expires_at,
    )


@pytest.fixture
def context():
    client = Client()
    clock = Clock()
    sizer = Sizer()
    repository = GameRepositoryDynamoDB(
        "games", client, clock, sizer, EncodedItemBudget()
    )
    return repository, client, clock, sizer


def test_create_uses_strong_reads_and_one_conditional_transaction(context):
    repository, client, _, sizer = context
    result = repository.create_game(game(), receipt())

    assert result == receipt()
    assert len(client.transactions) == 1
    assert len(client.transactions[0]["TransactItems"]) == 2
    assert client.gets[0]["ConsistentRead"] is True
    puts = [entry["Put"] for entry in
            client.transactions[0]["TransactItems"]]
    assert all(value["TableName"] == "games" for value in puts)
    assert all(value["ConditionExpression"] ==
               "attribute_not_exists(pk) OR ttl <= :now" for value in puts)
    assert sizer.items[0]["state"] == {"B": b"{}"}
    assert repository.load_game("game-1") == game()
    assert repository.find_receipt("a" * 64) == receipt()
    assert all(request["ConsistentRead"] is True for request in client.gets)


def test_commit_updates_every_non_key_game_attribute(context):
    repository, client, _, _ = context
    repository.create_game(game(), receipt())
    client.transactions.clear()

    repository.commit_command(
        1, game(version=2), receipt(version=2, key="c" * 64)
    )

    transaction = client.transactions[0]["TransactItems"]
    update = transaction[0]["Update"]
    assert update["ConditionExpression"] == (
        "#version = :expected_version AND #ttl > :now"
    )
    assert set(update["ExpressionAttributeNames"].values()) == (
        {name.removeprefix(":") for name in
         set(update["ExpressionAttributeValues"]) -
         {":expected_version", ":now"}}
    )
    assert transaction[1]["Put"]["ConditionExpression"] == (
        "attribute_not_exists(pk) OR ttl <= :now"
    )
    assert repository.load_game("game-1").version == 2


def test_matching_and_conflicting_receipts_precede_other_checks(context):
    repository, client, clock, sizer = context
    original = repository.create_game(game(expires_at=300),
                                      receipt(expires_at=300))
    clock.value = 200
    sizer.size = 999999
    client.transactions.clear()
    assert repository.commit_command(
        8, game(9, 300), receipt(9, expires_at=300)
    ) == original
    assert client.transactions == []
    with pytest.raises(IdempotencyConflictError):
        repository.commit_command(
            8, game(9, 300),
            receipt(9, fingerprint="c" * 64, expires_at=300),
        )


def test_oversized_item_sends_no_transaction(context):
    repository, client, _, sizer = context
    sizer.size = 358401
    with pytest.raises(PersistenceCapacityError):
        repository.create_game(game(), receipt())
    assert client.transactions == []


def test_malformed_item_and_read_failure_are_storage_neutral(context):
    repository, client, _, _ = context
    client.items[("GAME#game-1", "SNAPSHOT")] = {
        "pk": {"S": "GAME#game-1"}, "sk": {"S": "SNAPSHOT"}
    }
    with pytest.raises(PersistenceUnavailableError):
        repository.load_game("game-1")

    def fail(**request):
        raise EndpointConnectionError(endpoint_url="http://dynamodb")

    client.get_item = fail
    with pytest.raises(PersistenceUnavailableError):
        repository.find_receipt("a" * 64)


def test_cancelled_create_reconciles_live_game(context):
    repository, client, _, _ = context
    repository.create_game(game(), receipt())
    client.transaction_error = cancellation("ConditionalCheckFailed", "None")
    with pytest.raises(GameAlreadyExistsError):
        repository.create_game(game(), receipt(key="c" * 64))


def test_failed_commit_reconciles_missing_and_changed_games(context):
    repository, client, clock, _ = context
    client.transaction_error = cancellation("ConditionalCheckFailed", "None")
    with pytest.raises(GameNotFoundError):
        repository.commit_command(
            1, game(2), receipt(2, key="c" * 64)
        )

    client.transaction_error = None
    repository.create_game(game(), receipt())
    stored = client.items[("GAME#game-1", "SNAPSHOT")]
    stored["version"] = {"N": "3"}
    client.transaction_error = cancellation("ConditionalCheckFailed", "None")
    with pytest.raises(GameVersionConflictError) as caught:
        repository.commit_command(
            1, game(2), receipt(2, key="d" * 64)
        )
    assert caught.value.current_version == 3

    stored["version"] = {"N": "1"}
    with pytest.raises(PersistenceUnavailableError):
        repository.commit_command(
            1, game(2), receipt(2, key="e" * 64)
        )
    clock.value = 200
    with pytest.raises(GameNotFoundError):
        repository.commit_command(
            1, game(2, 300), receipt(2, key="f" * 64, expires_at=300)
        )


def cancellation(*codes):
    return ClientError({
        "Error": {"Code": "TransactionCanceledException",
                  "Message": "provider detail"},
        "CancellationReasons": [{"Code": code} for code in codes],
    }, "TransactWriteItems")
