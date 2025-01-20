from src.game.board import Board
from src.game.player import Player, PlayerType
from src.game.sparseboard import SparseBoard
from src.unit.faction import Faction
from src.unit.unit import Unit
import uuid


class Game:
    def __init__(self, players: list, board: Board):
        self.id = str(uuid.uuid4())
        self.players = players
        self.board = board

    def get_id(self):
        return self.id

    def get_board(self):
        return self.board

    def update(self, sparse_board: SparseBoard) -> None:
        # TODO
        print(f"update: {sparse_board}")

    def resolve_combat(self):
        # TODO
        pass

    def get_sparse_board(self):
        # TODO
        pass

    @staticmethod
    def create_sample_game():
        red_faction = Faction("Red Faction", "#C81010")
        player1 = Player("Player 1", PlayerType.HUMAN, [red_faction])

        blue_faction = Faction("Blue Faction", "#4682B4")
        player2 = Player("Player 2", PlayerType.CPU, [blue_faction])

        game = Game([player1, player2], Board(10, 10))

        red_unit = Unit("Red Unit", red_faction, "Infantry", 2, 2, 6)
        game.board.add_unit(red_unit, 6, 4)

        blue_unit = Unit("Blue Unit", blue_faction, "Infantry", 4, 4, 4)
        game.board.add_unit(blue_unit, 3, 5)

        return game
