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
from battle_hexes_api.samplegame import SampleGameCreator  # noqa: E402

app = FastAPI()


@app.get("/health")
def health():
    """Health check endpoint used by load balancers."""
    return {"status": "ok"}


game_repo = GameRepository()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/games')
def create_game():
    """Create a new sample game and store it in the repository."""
    new_game = SampleGameCreator.create_sample_game()
    game_repo.update_game(new_game)
    return new_game.to_game_model()


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
    return _get_game_or_404(game_id).to_game_model()


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
