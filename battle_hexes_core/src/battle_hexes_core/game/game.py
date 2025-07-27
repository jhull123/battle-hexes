from battle_hexes_core.game.board import Board, BoardModel
from battle_hexes_core.game.player import Player
from battle_hexes_core.game.sparseboard import SparseBoard
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from pydantic import BaseModel
from typing import List
import uuid


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

    def get_players(self):
        return self.players

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
        self.get_current_player().movement_cb()

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

    def play(self) -> None:
        """
        Start the game loop and play until the game is over. All players must
        be of type CPU.
        """
        pass
