from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.game.game import Game
from src.game.gamerepo import GameRepository

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


@app.put('/games/{game_id}')
def update_game(game):
    # TODO pick up here!
    game_repo.update_game(game)
    return None


@app.get('/games/{game_id}')
def get_game(game_id: str):
    return game_repo.get_game(game_id)
