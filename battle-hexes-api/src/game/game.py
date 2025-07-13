from src.cpu.randomplayer import RandomPlayer
from src.game.board import Board, BoardModel
from src.game.player import Player, PlayerType
from src.game.sparseboard import SparseBoard
from src.unit.faction import Faction
from src.unit.unit import Unit
from src.game.unitmovementplan import UnitMovementPlan
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
        if players:
            self.current_player = players[0]
        self.board = board

    def get_id(self):
        return self.id

    def get_board(self):
        return self.board

    def update(self, sparse_board: SparseBoard) -> None:
        self.board.update(sparse_board)

    def get_current_player(self) -> Player:
        return self.current_player

    def apply_movement_plans(self, plans: List["UnitMovementPlan"]) -> None:
        """Apply a collection of movement plans to update unit positions."""
        for plan in plans:
            if not plan.path:
                continue
            final_hex = plan.path[-1]
            plan.unit.set_coords(final_hex.row, final_hex.column)

    def next_player(self) -> Player:
        """Advance to the next player and return it."""
        if not self.players:
            return None
        idx = self.players.index(self.current_player)
        self.current_player = self.players[(idx + 1) % len(self.players)]
        return self.current_player

    def to_game_model(self) -> GameModel:
        return GameModel(
            id=self.id,
            players=self.players,
            board=self.board.to_board_model()
        )

    def get_opposing_factions(self, faction: Faction) -> List[Faction]:
        owning_player = self.get_player_for_faction(faction)
        opposing_factions = []
        for player in self.players:
            if player != owning_player:
                opposing_factions.extend(player.factions)
        return opposing_factions

    def get_player_for_faction(self, faction: Faction) -> Player:
        for player in self.players:
            if faction in player.factions:
                return player
        raise ValueError(f"No player found for faction {faction.name}")

    @staticmethod
    def create_sample_game():
        red_faction = Faction(
             id=UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479", version=4),
             name="Red Faction", color="#C81010")

        blue_faction = Faction(
             id=UUID("38400000-8cf0-11bd-b23e-10b96e4ef00d", version=4),
             name="Blue Faction", color="#4682B4")

        board = Board(10, 10)

        player1 = RandomPlayer(
            name="Player 1",
            type=PlayerType.CPU,
            factions=[red_faction],
            board=board
        )

        player2 = RandomPlayer(
            name="Player 2",
            type=PlayerType.CPU,
            factions=[blue_faction],
            board=board
        )

        game = Game([player1, player2], board)

        red_unit = Unit(
             UUID("a22c90d0-db87-11d0-8c3a-00c04fd708be", version=4),
             "Red Unit", red_faction, player1,
             "Infantry", 2, 2, 6)
        game.board.add_unit(red_unit, 6, 4)

        blue_unit = Unit(
             UUID("c9a440d2-2b0a-4730-b4c6-da394b642c61", version=4),
             "Blue Unit", blue_faction, player2,
             "Infantry", 4, 4, 4)
        game.board.add_unit(blue_unit, 3, 5)

        return game
