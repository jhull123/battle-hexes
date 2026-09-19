import hashlib
from dataclasses import FrozenInstanceError

import pytest

from battle_hexes_api.persistence import (
    CommandIdentity,
    CommandReceipt,
    EncodedItemBudget,
    GameRepository,
    GameVersionConflictError,
    PersistenceCapacityError,
    StoredGame,
    canonical_json_bytes,
    create_command_identity,
    digest_idempotency_key,
    fingerprint_request,
    is_expired,
    normalize_route,
)


DIGEST = "a" * 64
FINGERPRINT = "b" * 64


class FixedClock:
    def __init__(self, current_time):
        self.current_time = current_time

    def now(self):
        return self.current_time


def make_identity():
    return CommandIdentity(DIGEST, FINGERPRINT)


def make_game(**changes):
    values = {
        "game_id": "game-1",
        "version": 1,
        "state_schema_version": 1,
        "scenario_id": "scenario-1",
        "scenario_version": "1",
        "state": b"{}",
        "updated_at": 100,
        "expires_at": 200,
    }
    values.update(changes)
    return StoredGame(**values)


def make_receipt(headers=None, **changes):
    values = {
        "identity": make_identity(),
        "game_id": "game-1",
        "game_version": 1,
        "status_code": 201,
        "content_type": "application/json",
        "response_body": b'{"gameVersion":1}',
        "response_headers": headers or {"Game-Version": "1"},
        "created_at": 100,
        "expires_at": 200,
    }
    values.update(changes)
    return CommandReceipt(**values)


@pytest.mark.parametrize("length", [1, 255])
def test_idempotency_key_accepts_length_boundaries(length):
    key = "a" * length
    assert digest_idempotency_key(key) == hashlib.sha256(
        key.encode("ascii")
    ).hexdigest()


@pytest.mark.parametrize(
    "key",
    ["", "a" * 256, "with space", "with\ttab", "line\nbreak", "nul\0", "é"],
)
def test_idempotency_key_rejects_invalid_values(key):
    with pytest.raises(ValueError):
        digest_idempotency_key(key)


def test_command_identity_does_not_retain_or_render_raw_key():
    raw_key = "private-client-token"
    identity = create_command_identity(raw_key, "post", "/games", None, {})
    assert raw_key not in repr(identity)
    assert vars(identity) == {
        "key_digest": hashlib.sha256(raw_key.encode("ascii")).hexdigest(),
        "request_fingerprint": fingerprint_request(
            "POST", "/games", None, {}
        ),
    }


def test_canonical_json_is_stable_and_uses_utf8():
    first = {"z": "héx", "a": {"two": 2, "one": 1}}
    second = {"a": {"one": 1, "two": 2}, "z": "héx"}
    expected = b'{"a":{"one":1,"two":2},"z":"h\xc3\xa9x"}'
    assert canonical_json_bytes(first) == expected
    assert canonical_json_bytes(second) == expected


@pytest.mark.parametrize(
    "body",
    [{1: "bad"}, {"number": float("nan")}, {"number": float("inf")}, (1, 2)],
)
def test_canonical_json_rejects_non_json_values(body):
    with pytest.raises(ValueError):
        canonical_json_bytes(body)


def test_canonical_json_rejects_cycles():
    body = []
    body.append(body)
    with pytest.raises(ValueError):
        canonical_json_bytes(body)


def test_request_fingerprint_matches_fixed_vector():
    body = {"destination": {"column": 4, "row": 2}}
    assert fingerprint_request(
        "POST", "/games/6e6f/movements", 7, body
    ) == "472663844288c4822d7225dcea9c6dbc48603373b502d5fe99434f3b54bebcf7"


def test_request_fingerprint_normalizes_permitted_variations():
    body = {"z": 2, "a": 1}
    expected = fingerprint_request("post", "/games/a%2f/", 1, body)
    assert fingerprint_request(
        "POST", "/games/a%2F", 1, {"a": 1, "z": 2}
    ) == expected


@pytest.mark.parametrize(
    "changed",
    [
        ("PUT", "/games/one", 1, {"value": 1}),
        ("POST", "/games/two", 1, {"value": 1}),
        ("POST", "/games/one", 2, {"value": 1}),
        ("POST", "/games/one", 1, {"value": 2}),
    ],
)
def test_each_command_field_changes_fingerprint(changed):
    baseline = fingerprint_request(
        "POST", "/games/one", 1, {"value": 1}
    )
    assert fingerprint_request(*changed) != baseline


@pytest.mark.parametrize(
    "route",
    ["games/a", "//authority/path", "/games?a=1", "/games#part", "/bad%2"],
)
def test_route_rejects_non_path_or_ambiguous_values(route):
    with pytest.raises(ValueError):
        normalize_route(route)


def test_route_does_not_rewrite_path_content():
    assert normalize_route("/games/../Game//one") == "/games/../Game//one"
    assert normalize_route("/") == "/"


def test_persistence_values_are_frozen_and_receipt_headers_are_detached():
    headers = {"Game-Version": "1"}
    game = make_game()
    receipt = make_receipt(headers)
    headers["Game-Version"] = "2"
    assert receipt.response_headers == {"Game-Version": "1"}
    with pytest.raises(TypeError):
        receipt.response_headers["New"] = "value"
    with pytest.raises(FrozenInstanceError):
        game.version = 2


@pytest.mark.parametrize(
    "change",
    [
        {"version": 0},
        {"version": True},
        {"state_schema_version": 0},
        {"state": b"\xff"},
        {"state": "{}"},
        {"expires_at": 100},
    ],
)
def test_stored_game_rejects_invalid_invariants(change):
    with pytest.raises(ValueError):
        make_game(**change)


def test_receipt_rejects_invalid_invariants():
    with pytest.raises(ValueError):
        make_receipt(status_code=99)
    with pytest.raises(ValueError):
        make_receipt(response_headers={"Header": 1})
    with pytest.raises(ValueError):
        make_receipt(expires_at=100)


def test_logical_expiry_uses_inclusive_boundary_and_injected_clock():
    clock = FixedClock(200)
    assert is_expired(200, clock)
    assert not is_expired(201, clock)


def test_item_budget_accepts_limit_and_reports_overage_metadata():
    budget = EncodedItemBudget()
    assert budget.require_fits("game", 358400) is None
    with pytest.raises(PersistenceCapacityError) as raised:
        budget.require_fits("receipt", 358401)
    assert raised.value.item_kind == "receipt"
    assert raised.value.measured_bytes == 358401
    assert raised.value.limit_bytes == 358400


def test_version_conflict_exposes_only_storage_neutral_metadata():
    error = GameVersionConflictError(expected_version=7, current_version=8)
    assert error.expected_version == 7
    assert error.current_version == 8


def test_minimal_repository_satisfies_runtime_protocol_shape():
    class FakeRepository:
        def load_game(self, game_id):
            return make_game(game_id=game_id)

        def find_receipt(self, key_digest):
            return None

        def create_game(self, game, receipt):
            return None

        def commit_command(self, expected_version, game, receipt):
            return None

    repository: GameRepository = FakeRepository()
    assert repository.load_game("game-2").game_id == "game-2"
