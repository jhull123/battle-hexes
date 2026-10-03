"""FastAPI application composition for game persistence."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from battle_hexes_api.game_routes import router as game_router
from battle_hexes_api.health import router as health_router
from battle_hexes_api.health.startup import dependency_lifespan
from battle_hexes_api.persistence import (
    EncodedItemBudget,
    GameCommandService,
    GameRepositoryDynamoDB,
    GameRepositoryInMemory,
    GameStateCodec,
    InstrumentedGameRepository,
    SystemClock,
)
from battle_hexes_api.persistence.item_sizer import InMemoryItemSizer
from battle_hexes_api.persistence.dynamodb_codec import (
    encode_game as encode_dynamodb_game,
    encode_receipt as encode_dynamodb_receipt,
)
from battle_hexes_api.persistence.in_memory import (
    _game_item as encode_memory_game,
    _receipt_item as encode_memory_receipt,
)
from battle_hexes_api.persistence import CommandServiceError


def create_app(
    *, clock=None, repository=None, codec=None, telemetry_sink=None
):
    """Create an isolated application, optionally injecting persistence."""
    runtime_clock = clock or SystemClock()
    runtime_codec = codec or GameStateCodec()

    @asynccontextmanager
    async def lifespan(app):
        async with dependency_lifespan(app):
            runtime_repository = repository or _configured_repository(
                app, runtime_clock
            )
            instrumented_repository = _instrument_repository(
                runtime_repository, telemetry_sink
            )
            app.state.game_repository = runtime_repository
            app.state.game_command_service = GameCommandService(
                instrumented_repository, runtime_codec, runtime_clock
            )
            app.state.game_state_codec = runtime_codec
            yield

    app = FastAPI(lifespan=lifespan)

    @app.exception_handler(CommandServiceError)
    async def command_error_handler(
        _request: Request, error: CommandServiceError
    ):
        return JSONResponse(error.as_dict(), status_code=error.status_code)

    app.include_router(health_router)
    app.include_router(game_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Game-Version"],
    )
    return app


def _configured_repository(app, clock):
    config = app.state.dynamodb_config
    sizer = InMemoryItemSizer()
    budget = EncodedItemBudget()
    if config.enabled:
        return GameRepositoryDynamoDB(
            config.table_name,
            app.state.dynamodb_client,
            clock,
            sizer,
            budget,
        )
    return GameRepositoryInMemory(clock, sizer, budget)


def _instrument_repository(repository, sink):
    is_dynamodb = isinstance(repository, GameRepositoryDynamoDB)
    implementation = "dynamodb" if is_dynamodb else "in_memory"
    game_encoder = encode_dynamodb_game if is_dynamodb else encode_memory_game
    receipt_encoder = (
        encode_dynamodb_receipt if is_dynamodb else encode_memory_receipt
    )
    return InstrumentedGameRepository(
        repository,
        implementation,
        repository._item_sizer,
        game_encoder,
        receipt_encoder,
        sink=sink,
    )
