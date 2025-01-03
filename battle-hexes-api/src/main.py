from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.game.board import Board
from src.game.game import Game

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/games')
def create_game():
  return Game(Board(10, 10))
