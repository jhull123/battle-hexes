"""HTTP adaptation for authoritative game queries and commands."""

import re

from fastapi import APIRouter, Body, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from battle_hexes_api.command_adapters import (
    CombatAdapter,
    CombatResponseSerializer,
    CreateGameAdapter,
    CreateGameResponseSerializer,
    EndMovementAdapter,
    EndTurnAdapter,
    EndTurnResponseSerializer,
    GameAlreadyCompletedError,
    GameResponseSerializer,
    HumanMoveAdapter,
    MovementAdapter,
    MovementResponseSerializer,
)
from battle_hexes_api.persistence import CommandRequest, CommandServiceError
from battle_hexes_api.persistence.command_errors import CommandErrorTranslator
from battle_hexes_api.persistence.identity import digest_idempotency_key
from battle_hexes_api.player_types import list_player_types
from battle_hexes_api.schemas import (
    CreateGameRequest,
    PlayerTypeModel,
    ScenarioModel,
    SparseBoard,
)
from battle_hexes_core.scenario.scenario_loader import load_scenario
from battle_hexes_core.scenario.scenarioregistry import ScenarioRegistry

router = APIRouter()
scenario_registry = ScenarioRegistry()
_VERSION_PATTERN = re.compile(r"[1-9][0-9]*\Z")


def _body(value):
    if value is None:
        return {}
    return value.model_dump(by_alias=True, mode="json")


def _command_request(idempotency_key, expected_version, route, body):
    try:
        digest_idempotency_key(idempotency_key)
    except ValueError:
        raise CommandErrorTranslator.error(
            400, "invalidIdempotencyKey"
        ) from None
    if expected_version is not None and not _VERSION_PATTERN.fullmatch(
        expected_version
    ):
        raise CommandErrorTranslator.error(
            400, "invalidExpectedGameVersion"
        )
    return CommandRequest(
        idempotency_key=idempotency_key or "",
        method="POST",
        normalized_route=route,
        validated_body=_body(body),
        expected_game_version=(
            int(expected_version) if expected_version is not None else None
        ),
    )


def _response(success):
    return Response(
        content=success.body,
        status_code=success.status_code,
        media_type=success.content_type,
        headers=dict(success.headers),
    )


def _error_response(error):
    return JSONResponse(error.as_dict(), status_code=error.status_code)


def _execute(request, game_id, route, key, version, body, adapter, serializer):
    command = _command_request(key, version, route, body)
    try:
        success = request.app.state.game_command_service.execute(
            game_id, command, adapter, serializer
        )
    except GameAlreadyCompletedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except CommandServiceError as error:
        return _error_response(error)
    return _response(success)


@router.post("/games")
def create_game(
    request: Request,
    payload: CreateGameRequest,
    idempotency_key: str | None = Header(None),
):
    command = _command_request(idempotency_key, None, "/games", payload)
    try:
        success = request.app.state.game_command_service.create(
            command,
            CreateGameAdapter(payload),
            CreateGameResponseSerializer(None),
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404, detail="Scenario not found"
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except CommandServiceError as error:
        return _error_response(error)
    return _response(success)


@router.get("/games/{game_id}")
def get_game(request: Request, game_id: str):
    try:
        stored = request.app.state.game_repository.load_game(game_id)
        game = request.app.state.game_state_codec.decode(stored)
        serializer = GameResponseSerializer(
            stored.scenario_version, load_scenario
        )
        status, body, content_type, headers = serializer(
            game, None, stored.version
        )
        headers["Game-Version"] = str(stored.version)
        return Response(body, status, headers, content_type)
    except Exception as error:
        if isinstance(error, HTTPException):
            raise
        translated = CommandErrorTranslator.translate_read(error, game_id)
        return _error_response(translated)


def _headers(key, version):
    return key, version


@router.post("/games/{game_id}/movement")
def generate_movement(request: Request, game_id: str,
                      idempotency_key: str | None = Header(None),
                      expected_game_version: str | None = Header(None)):
    key, version = _headers(idempotency_key, expected_game_version)
    return _execute(request, game_id, f"/games/{game_id}/movement", key,
                    version, None, MovementAdapter(),
                    _movement_serializer(request, game_id))


def _movement_serializer(request, game_id):
    return MovementResponseSerializer(None)


@router.post("/games/{game_id}/move")
def resolve_human_move(request: Request, game_id: str,
                       sparse_board: SparseBoard = Body(...),
                       idempotency_key: str | None = Header(None),
                       expected_game_version: str | None = Header(None)):
    return _execute(request, game_id, f"/games/{game_id}/move",
                    idempotency_key, expected_game_version, sparse_board,
                    HumanMoveAdapter(sparse_board),
                    _movement_serializer(request, game_id))


@router.post("/games/{game_id}/end-movement")
def end_movement(request: Request, game_id: str,
                 sparse_board: SparseBoard = Body(...),
                 idempotency_key: str | None = Header(None),
                 expected_game_version: str | None = Header(None)):
    return _execute(request, game_id, f"/games/{game_id}/end-movement",
                    idempotency_key, expected_game_version, sparse_board,
                    EndMovementAdapter(sparse_board),
                    _movement_serializer(request, game_id))


@router.post("/games/{game_id}/combat")
def resolve_combat(request: Request, game_id: str,
                   sparse_board: SparseBoard = Body(...),
                   idempotency_key: str | None = Header(None),
                   expected_game_version: str | None = Header(None)):
    return _execute(request, game_id, f"/games/{game_id}/combat",
                    idempotency_key, expected_game_version, sparse_board,
                    CombatAdapter(sparse_board), CombatResponseSerializer())


@router.post("/games/{game_id}/end-turn")
def end_turn(request: Request, game_id: str,
             sparse_board: SparseBoard = Body(...),
             idempotency_key: str | None = Header(None),
             expected_game_version: str | None = Header(None)):
    serializer = EndTurnResponseSerializer(None)
    return _execute(request, game_id, f"/games/{game_id}/end-turn",
                    idempotency_key, expected_game_version, sparse_board,
                    EndTurnAdapter(sparse_board), serializer)


@router.get("/scenarios", response_model=list[ScenarioModel])
def list_scenarios():
    return [
        ScenarioModel.from_core(s)
        for s in scenario_registry.list_scenarios()
    ]


@router.get("/player-types", response_model=list[PlayerTypeModel])
def get_player_types():
    return [
        PlayerTypeModel.from_definition(item)
        for item in list_player_types()
    ]
