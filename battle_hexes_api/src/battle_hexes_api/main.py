from fastapi import FastAPI
from fastapi import Body
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Allow running the API without installing the sibling packages by adding them
# to ``sys.path`` relative to this file. This lets ``fastapi dev src/main.py``
# work when executed from inside ``battle_hexes_api``.
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
print("Repo root:", REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "battle_hexes_core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "battle_agent_rl" / "src"))
print("sys.path:", sys.path)

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


@app.get('/games/{game_id}')
def get_game(game_id: str):
    return _get_game_or_404(game_id).to_game_model()


@app.post('/games/{game_id}/combat')
def resolve_combat(
    game_id: str,
    sparse_board: SparseBoard = Body(...)
) -> SparseBoard:
    print(f'We got game: {game_id}')
    game = _get_game_or_404(game_id)
    game.update(sparse_board)

    results = Combat(game).resolve_combat()
    print('Combat results:', results)

    game_repo.update_game(game)
    sparse_board = game.get_board().to_sparse_board()
    sparse_board.last_combat_results = results.battles_as_result_schema()
    return sparse_board


@app.post('/games/{game_id}/movement')
def generate_movement(game_id: str):
    """Generate and apply movement plans for the current player."""
    game = _get_game_or_404(game_id)
    current_player = game.get_current_player()
    print(f"Generating movement for player: {current_player.name}")
    plans = current_player.movement()
    game.apply_movement_plans(plans)
    game_repo.update_game(game)
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
    print(
        f"The turn has ended for player: {old_player.name}. "
        f"Now it's {new_player.name}'s turn."
    )

    game_repo.update_game(game)
    return game.to_game_model()
