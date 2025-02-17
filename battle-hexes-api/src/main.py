from fastapi import FastAPI
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from src.combat.combat import Combat
from src.game.game import Game
from src.game.gamerepo import GameRepository
from src.game.sparseboard import SparseBoard

app = FastAPI()
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
    new_game = Game.create_sample_game()
    game_repo.update_game(new_game)
    return new_game.to_game_model()


@app.get('/games/{game_id}')
def get_game(game_id: str):
    return game_repo.get_game(game_id).to_game_model()


@app.post('/games/{game_id}/combat')
def resolve_combat(
    game_id: str,
    sparse_board: SparseBoard = Body(...)
) -> SparseBoard:
    print(f'we got game: {game_id}')
    game = game_repo.get_game(game_id)
    game.update(sparse_board)

    results = Combat(game).resolve_combat()
    print('combat results:', results)

    game_repo.update_game(game)
    return game.get_board().to_sparse_board()
