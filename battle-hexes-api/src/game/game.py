import uuid

class Game:
  def __init__(self):
    self.id = str(uuid.uuid4())

  def get_id(self):
    return self.id
