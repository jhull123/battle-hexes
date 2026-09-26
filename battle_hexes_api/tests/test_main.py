from fastapi.testclient import TestClient

from battle_hexes_api.application import create_app


CREATE = {"scenarioId": "elim_1", "playerTypes": ["human", "random"]}


def create(client, key="create-12345678"):
    return client.post("/games", json=CREATE, headers={"Idempotency-Key": key})


def test_health_and_static_routes_remain_available():
    with TestClient(create_app()) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/ready").status_code == 200
        assert client.get("/scenarios").status_code == 200
        assert client.get("/player-types").status_code == 200


def test_create_replay_and_get_use_authoritative_versioned_storage():
    with TestClient(create_app()) as client:
        first = create(client)
        replay = create(client)
        game_id = first.json()["id"]
        loaded = client.get(f"/games/{game_id}")

        assert first.status_code == 200
        assert first.content == replay.content
        assert first.headers["game-version"] == "1"
        assert first.json()["gameVersion"] == 1
        assert first.json()["scenarioVersion"]
        assert loaded.status_code == 200
        assert loaded.headers["game-version"] == "1"
        assert loaded.json()["gameVersion"] == 1
        assert (
            loaded.json()["scenarioVersion"]
            == first.json()["scenarioVersion"]
        )


def test_command_headers_are_required_before_execution():
    with TestClient(create_app()) as client:
        game_id = create(client).json()["id"]
        missing_key = client.post(f"/games/{game_id}/movement")
        missing_version = client.post(
            f"/games/{game_id}/movement",
            headers={"Idempotency-Key": "move-12345678"},
        )
        invalid_version = client.post(
            f"/games/{game_id}/movement",
            headers={
                "Idempotency-Key": "move-12345678",
                "Expected-Game-Version": "+1",
            },
        )

        assert missing_key.status_code == 400
        assert missing_key.json()["code"] == "invalidIdempotencyKey"
        assert missing_version.status_code == 428
        assert missing_version.json()["code"] == "expectedGameVersionRequired"
        assert invalid_version.status_code == 400
        assert invalid_version.json()["code"] == "invalidExpectedGameVersion"
        assert client.get(f"/games/{game_id}").json()["gameVersion"] == 1


def test_successful_existing_command_advances_once_and_replays():
    with TestClient(create_app()) as client:
        game_id = create(client).json()["id"]
        headers = {
            "Idempotency-Key": "movement-12345678",
            "Expected-Game-Version": "1",
        }
        first = client.post(f"/games/{game_id}/movement", headers=headers)
        replay = client.post(f"/games/{game_id}/movement", headers=headers)

        assert first.status_code == 200
        assert first.content == replay.content
        assert first.headers["game-version"] == "2"
        assert first.json()["gameVersion"] == 2
        assert client.get(f"/games/{game_id}").json()["gameVersion"] == 2


def test_stale_command_returns_structured_conflict():
    with TestClient(create_app()) as client:
        game_id = create(client).json()["id"]
        client.post(
            f"/games/{game_id}/movement",
            headers={
                "Idempotency-Key": "movement-12345678",
                "Expected-Game-Version": "1",
            },
        )
        conflict = client.post(
            f"/games/{game_id}/movement",
            headers={
                "Idempotency-Key": "movement-87654321",
                "Expected-Game-Version": "1",
            },
        )

        assert conflict.status_code == 409
        assert conflict.json() == {
            "code": "gameVersionConflict",
            "message": "The game version has changed.",
            "gameId": game_id,
            "expectedGameVersion": 1,
            "currentGameVersion": 2,
        }


def test_cors_exposes_and_accepts_persistence_headers():
    with TestClient(create_app()) as client:
        response = client.options(
            "/games/example/movement",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": (
                    "Idempotency-Key, Expected-Game-Version"
                ),
            },
        )
        assert response.status_code == 200
        allowed = response.headers["access-control-allow-headers"].lower()
        assert "idempotency-key" in allowed
        created = client.post(
            "/games",
            json=CREATE,
            headers={
                "Idempotency-Key": "cors-create-1234",
                "Origin": "https://example.test",
            },
        )
        assert (
            created.headers["access-control-expose-headers"]
            == "Game-Version"
        )
