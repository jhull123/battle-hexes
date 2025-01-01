from fastapi import FastAPI
from game.game import Game

app = FastAPI()

@app.post('/games')
def create_game():
  return Game()
