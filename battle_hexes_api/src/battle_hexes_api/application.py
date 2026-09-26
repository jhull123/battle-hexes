"""FastAPI application composition for game persistence."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from battle_hexes_api.game_routes import router as game_router
from battle_hexes_api.health import router as health_router
from battle_hexes_api.health.readiness import configure_readiness
from battle_hexes_api.persistence import (
    EncodedItemBudget,
    GameCommandService,
    GameRepositoryInMemory,
    GameStateCodec,
    SystemClock,
)
from battle_hexes_api.persistence.item_sizer import InMemoryItemSizer
from battle_hexes_api.persistence import CommandServiceError


def create_app(*, clock=None, repository=None, codec=None):
    """Create an isolated application, optionally injecting persistence."""
    runtime_clock = clock or SystemClock()
    runtime_codec = codec or GameStateCodec()
    runtime_repository = repository or GameRepositoryInMemory(
        runtime_clock, InMemoryItemSizer(), EncodedItemBudget()
    )

    @asynccontextmanager
    async def lifespan(app):
        configure_readiness(app)
        app.state.game_repository = runtime_repository
        app.state.game_command_service = GameCommandService(
            runtime_repository, runtime_codec, runtime_clock
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
