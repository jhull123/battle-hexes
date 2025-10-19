from fastapi import FastAPI
from fastapi import Body
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
logger.info("Repo root: %s", REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "battle_hexes_core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "battle_agent_rl" / "src"))
logger.info("sys.path: %s", sys.path)

from battle_hexes_core.combat.combat import Combat  # noqa: E402
from battle_hexes_core.game.gamerepo import GameRepository  # noqa: E402
from battle_hexes_core.game.sparseboard import SparseBoard  # noqa: E402
from battle_hexes_core.scenario.scenarioregistry import (  # noqa: E402
    ScenarioRegistry,
)
from battle_hexes_api.player_types import list_player_types  # noqa: E402
from battle_hexes_api.gamecreator import GameCreator  # noqa: E402
from battle_hexes_api.schemas import (  # noqa: E402
    CreateGameRequest,
    PlayerModel,
    PlayerTypeModel,
    ScenarioModel,
)

app = FastAPI()


@app.get("/health")
def health():
    """Health check endpoint used by load balancers."""
    return {"status": "ok"}


game_repo = GameRepository()
scenario_registry = ScenarioRegistry()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize_game(game) -> dict:
    """Return a JSON-serialisable representation of ``game``."""

    game_model = game.to_game_model()
    model = game_model.model_dump()
    model["players"] = [
        PlayerModel.from_core(player).model_dump()
        for player in game_model.players
    ]

    scenario_id = getattr(game, "scenario_id", None)
    if scenario_id is not None:
        model["scenarioId"] = scenario_id

    player_type_ids = getattr(game, "player_type_ids", None)
    if player_type_ids is not None:
        model["playerTypeIds"] = list(player_type_ids)

    return model


@app.post('/games')
def create_game(payload: CreateGameRequest):
    """Create a new sample game and store it in the repository."""

    try:
        scenario_registry.get_scenario(payload.scenario_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail="Scenario not found",
        ) from exc

    try:
        new_game = GameCreator.create_sample_game(
            payload.scenario_id, payload.player_types
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    game_repo.update_game(new_game)
    return _serialize_game(new_game)


@app.get("/scenarios", response_model=list[ScenarioModel])
def list_scenarios() -> list[ScenarioModel]:
    """Return the available scenarios registered in the core package."""

    scenarios = scenario_registry.list_scenarios()
    return [ScenarioModel.from_core(s) for s in scenarios]


@app.get("/player-types", response_model=list[PlayerTypeModel])
def get_player_types() -> list[PlayerTypeModel]:
    """Return the supported player types available on the platform."""

    return [
        PlayerTypeModel.from_definition(definition)
        for definition in list_player_types()
    ]


def _get_game_or_404(game_id: str):
    """Return the game for ``game_id`` or raise a 404 error."""
    try:
        return game_repo.get_game(game_id)
    except (KeyError, ValueError):
        raise HTTPException(status_code=404, detail="Game not found")


def _call_end_game_callbacks(game) -> None:
    """Invoke each player's ``end_game_cb`` if the game is over."""
    if game.is_game_over():
        for player in game.get_players():
            player.end_game_cb()


@app.get('/games/{game_id}')
def get_game(game_id: str):
    return _serialize_game(_get_game_or_404(game_id))


@app.post('/games/{game_id}/combat')
def resolve_combat(
    game_id: str,
    sparse_board: SparseBoard = Body(...)
) -> SparseBoard:
    logger.info("We got game: %s", game_id)
    game = _get_game_or_404(game_id)
    game.update(sparse_board)

    results = Combat(game).resolve_combat()
    logger.info('Combat results: %s', results)

    game_repo.update_game(game)
    _call_end_game_callbacks(game)
    sparse_board = game.get_board().to_sparse_board()
    sparse_board.last_combat_results = results.battles_as_result_schema()
    return sparse_board


@app.post('/games/{game_id}/movement')
def generate_movement(game_id: str):
    """Generate and apply movement plans for the current player."""
    game = _get_game_or_404(game_id)
    current_player = game.get_current_player()
    logger.info("Generating movement for player: %s", current_player.name)
    plans = current_player.movement()
    game.apply_movement_plans(plans)
    game_repo.update_game(game)
    _call_end_game_callbacks(game)
    return {
        "game": game.to_game_model(),
        "plans": [p.to_dict() for p in plans],
    }


@app.post('/games/{game_id}/end-turn')
def end_turn(game_id: str, sparse_board: SparseBoard = Body(...)):
    """Update game state at the end of a player's turn."""
    game = _get_game_or_404(game_id)

    # sync the server-side board state with the client provided one
    game.update(sparse_board)

    old_player = game.get_current_player()
    new_player = game.next_player()
    logger.info(
        "The turn has ended for player: %s. Now it's %s's turn.",
        old_player.name,
        new_player.name,
    )

    game_repo.update_game(game)
    _call_end_game_callbacks(game)
    return game.to_game_model()
