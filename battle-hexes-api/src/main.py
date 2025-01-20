from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    return new_game


@app.get('/games/{game_id}')
def get_game(game_id: str):
    return game_repo.get_game(game_id)


@app.post('/combat/{game_id}')
def resolve_combat(game_id: str, sparse_board: SparseBoard) -> SparseBoard:
    game = game_repo.get_game(game_id)
    game.update(sparse_board)
    game.resolve_combat()
    return game.get_sparse_board()
