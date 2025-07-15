from uuid import UUID


class GameRepository:
    def __init__(self):
        self.games = {}

    def update_game(self, game):
        self.games[self.to_uuid(game.get_id())] = game

    def get_game(self, game_id: UUID):
        return self.games[self.to_uuid(game_id)]

    def to_uuid(self, id: str):
        if not isinstance(id, UUID):
            return UUID(id)
        return id
