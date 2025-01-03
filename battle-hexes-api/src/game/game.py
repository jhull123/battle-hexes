import uuid

class Game:
  def __init__(self, board):
    self.id = str(uuid.uuid4())
    self.board = board

  def get_id(self):
    return self.id

  def get_board(self):
    return self.board