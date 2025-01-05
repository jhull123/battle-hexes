class GameRepository:
  def __init__(self):
    self.games = {}

  def update_game(self, game):
    self.games[game.get_id()] = game

  def get_game(self, game_id):
    return self.games[game_id]