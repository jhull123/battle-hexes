from src.game.board import Board, BoardModel
from src.game.player import Player, PlayerType
from src.game.sparseboard import SparseBoard
from src.unit.faction import Faction
from src.unit.unit import Unit
from pydantic import BaseModel
from typing import List
import uuid
from uuid import UUID


class GameModel(BaseModel):
    id: uuid.UUID
    players: List[Player]
    board: BoardModel


class Game:
    def __init__(self, players: list, board: Board):
        self.id = uuid.uuid4()
        self.players = players
        self.board = board

    def get_id(self):
        return self.id

    def get_board(self):
        return self.board

    def update(self, sparse_board: SparseBoard) -> None:
        self.board.update(sparse_board)

    def resolve_combat(self):
        # TODO
        pass

    def to_game_model(self) -> GameModel:
        return GameModel(
            id=self.id,
            players=self.players,
            board=self.board.to_board_model()
        )

    @staticmethod
    def create_sample_game():
        red_faction = Faction(
             id=UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479", version=4),
             name="Red Faction", color="#C81010")
        player1 = Player(name="Player 1",
                         type=PlayerType.HUMAN,
                         factions=[red_faction])

        blue_faction = Faction(
             id=UUID("38400000-8cf0-11bd-b23e-10b96e4ef00d", version=4),
             name="Blue Faction", color="#4682B4")
        player2 = Player(name="Player 2",
                         type=PlayerType.CPU,
                         factions=[blue_faction])

        game = Game([player1, player2], Board(10, 10))

        red_unit = Unit(
             UUID("a22c90d0-db87-11d0-8c3a-00c04fd708be", version=4),
             "Red Unit", red_faction, "Infantry", 2, 2, 6)
        game.board.add_unit(red_unit, 6, 4)

        blue_unit = Unit(
             UUID("c9a440d2-2b0a-4730-b4c6-da394b642c61", version=4),
             "Blue Unit", blue_faction, "Infantry", 4, 4, 4)
        game.board.add_unit(blue_unit, 3, 5)

        return game
