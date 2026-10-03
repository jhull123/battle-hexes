from dataclasses import dataclass

import pytest

from battle_hexes_api.persistence import (
    CommandRequest,
    CommandServiceError,
    CreatedGame,
    EncodedItemBudget,
    GameCommandService,
    GameRepositoryInMemory,
    PersistenceUnavailableError,
    SuccessfulResponse,
    digest_idempotency_key,
)


class Clock:
    def __init__(self, now=100):
        self.current = now

    def now(self):
        return self.current


class Sizer:
    def size_bytes(self, item):
        return 1


@dataclass
class Game:
    id: str
    scenario_id: str = "scenario-1"
    value: int = 0

    def get_id(self):
        return self.id


class Codec:
    STATE_SCHEMA_VERSION = 1

    def __init__(self):
        self.games = {}
        self.decode_count = 0
        self.encode_count = 0

    def encode(self, game, *, scenario_version):
        self.encode_count += 1
        self.games[(game.id, game.value)] = Game(
            game.id, game.scenario_id, game.value
        )
        return f'{{"value":{game.value}}}'.encode()

    def decode(self, stored):
        self.decode_count += 1
        value = int(stored.state.decode().split(":")[1][:-1])
        return Game(stored.game_id, stored.scenario_id, value)


def request(key="key-1", expected=None, route="/games"):
    return CommandRequest(key, "POST", route, {"amount": 1}, expected)


def response(game, result, version):
    marker = result if result is not None else "created"
    return SuccessfulResponse(
        201,
        f'{{"marker":"{marker}","gameVersion":{version}}}'.encode(),
        "application/json",
        {"game-version": str(version), "Date": "discard me", "X-App": "ok"},
        version,
    )


@pytest.fixture
def context():
    clock = Clock()
    repository = GameRepositoryInMemory(clock, Sizer(), EncodedItemBudget())
    codec = Codec()
    service = GameCommandService(repository, codec, clock)
    return service, repository, codec, clock


def create(service, key="key-1"):
    return service.create(
        request(key),
        lambda: CreatedGame(Game("game-1"), "scenario-1", "v1"),
        response,
    )


def test_create_commits_version_one_and_exact_finalized_response(context):
    service, repository, _, _ = context
    result = create(service)

    assert result.body == b'{"marker":"created","gameVersion":1}'
    assert result.headers == {"Game-Version": "1", "X-App": "ok"}
    assert repository.load_game("game-1").version == 1
    receipt = repository.find_receipt(digest_idempotency_key("key-1"))
    assert result.body == receipt.response_body
    assert result.content_type == receipt.content_type


def test_matching_retry_replays_before_creation_or_serialization(context):
    service, _, codec, clock = context
    original = create(service)
    clock.current = 200
    calls = []

    replay = service.create(
        request(),
        lambda: calls.append("create"),
        lambda *args: calls.append("serialize"),
    )

    assert replay == original
    assert calls == []
    assert codec.encode_count == 1


def test_changed_command_reusing_key_fails_before_game_load(context):
    service, _, codec, _ = context
    create(service)

    with pytest.raises(CommandServiceError) as raised:
        service.execute(
            "game-1",
            request(expected=1, route="/games/game-1/moves"),
            lambda game: pytest.fail("handler ran"),
            response,
        )

    assert raised.value.code == "idempotencyKeyReused"
    assert codec.decode_count == 0


def test_unique_existing_command_advances_and_stale_command_conflicts(context):
    service, repository, _, _ = context
    create(service)
    apply_count = 0

    def apply(game):
        nonlocal apply_count
        apply_count += 1
        game.value += 1
        return "moved"

    result = service.execute(
        "game-1", request("key-2", 1, "/games/game-1/moves"), apply,
        response,
    )
    assert result.game_version == 2
    assert repository.load_game("game-1").version == 2

    with pytest.raises(CommandServiceError) as raised:
        service.execute(
            "game-1",
            request("key-3", 1, "/games/game-1/end-turn"),
            apply,
            response,
        )
    assert raised.value.as_dict() == {
        "code": "gameVersionConflict",
        "message": "The game version has changed.",
        "gameId": "game-1",
        "expectedGameVersion": 1,
        "currentGameVersion": 2,
    }
    assert apply_count == 1


def test_matching_stale_retry_replays_without_loading_or_applying(context):
    service, _, codec, _ = context
    create(service)
    command = request("key-2", 1, "/games/game-1/moves")
    original = service.execute(
        "game-1", command, lambda game: "random-17", response
    )
    decode_count = codec.decode_count

    replay = service.execute(
        "game-1",
        command,
        lambda game: pytest.fail("handler ran"),
        lambda *args: pytest.fail("serializer ran"),
    )
    assert replay.body == original.body
    assert codec.decode_count == decode_count


def test_handler_or_serializer_failure_leaves_key_reusable(context):
    service, repository, _, _ = context
    create(service)
    command = request("retry-key", 1, "/games/game-1/moves")

    with pytest.raises(RuntimeError, match="failed"):
        service.execute(
            "game-1", command, lambda game: (_ for _ in ()).throw(
                RuntimeError("failed")
            ), response,
        )
    assert repository.load_game("game-1").version == 1

    with pytest.raises(RuntimeError, match="serialize"):
        service.execute(
            "game-1", command, lambda game: "result",
            lambda *args: (_ for _ in ()).throw(RuntimeError("serialize")),
        )
    assert repository.load_game("game-1").version == 1

    result = service.execute(
        "game-1", command, lambda game: "success", response
    )
    assert result.game_version == 2


class AmbiguousRepository:
    def __init__(self, repository, publish=False):
        self.repository = repository
        self.publish = publish
        self.pending_receipt = None
        self.load_count = 0

    def find_receipt(self, key):
        return self.repository.find_receipt(key)

    def load_game(self, game_id):
        self.load_count += 1
        return self.repository.load_game(game_id)

    def create_game(self, game, receipt):
        return self.repository.create_game(game, receipt)

    def commit_command(self, expected, game, receipt):
        if self.publish:
            self.repository.commit_command(expected, game, receipt)
        raise PersistenceUnavailableError()


def test_ambiguous_commit_replays_visible_receipt_without_rerun(context):
    _, repository, codec, clock = context
    service = GameCommandService(
        AmbiguousRepository(repository, publish=True), codec, clock
    )
    create(service)
    calls = []
    result = service.execute(
        "game-1",
        request("key-2", 1, "/games/game-1/moves"),
        lambda game: calls.append("apply") or "won",
        response,
    )
    assert result.game_version == 2
    assert calls == ["apply"]


def test_ambiguous_commit_with_unchanged_game_returns_unavailable(context):
    _, repository, codec, clock = context
    wrapper = AmbiguousRepository(repository)
    service = GameCommandService(wrapper, codec, clock)
    create(service)

    with pytest.raises(CommandServiceError) as raised:
        service.execute(
            "game-1",
            request("key-2", 1, "/games/game-1/moves"),
            lambda game: "result",
            response,
        )
    assert raised.value.status_code == 503
    assert raised.value.code == "gamePersistenceUnavailable"
    assert wrapper.load_count == 2


@pytest.mark.parametrize(
    ("expected", "status", "code"),
    [
        (None, 428, "expectedGameVersionRequired"),
        (0, 400, "invalidExpectedGameVersion"),
        (True, 400, "invalidExpectedGameVersion"),
    ],
)
def test_existing_request_invariants_precede_receipt_lookup(
    context, expected, status, code
):
    service, _, _, _ = context
    with pytest.raises(CommandServiceError) as raised:
        service.execute(
            "game-1", request(expected=expected), lambda game: None,
            response,
        )
    assert (raised.value.status_code, raised.value.code) == (status, code)
