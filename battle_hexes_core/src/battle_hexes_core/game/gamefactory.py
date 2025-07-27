from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player
from battle_hexes_core.unit.unit import Unit


class GameFactory:
    """Factory for generating ``Game`` instances from preset components."""

    def __init__(
        self,
        board_size: tuple[int, int],
        players: list[Player],
        units: list[Unit],
    ) -> None:
        self.board_size = board_size
        self.players = players
        self.units = units

        # Record the starting coordinates of each unit so they can be reset on
        # each ``create_game`` call.
        self._unit_start_positions = {
            unit: unit.get_coords() for unit in units
        }

    def create_game(self) -> Game:
        """Create a ``Game`` using the stored board size, players and units."""
        rows, cols = self.board_size
        # Always create a fresh board for a new game and assign it to players
        board = Board(rows, cols)
        for player in self.players:
            if hasattr(player, "_board"):
                player._board = board

        game = Game(self.players, board)

        for unit in self.units:
            coords = self._unit_start_positions.get(unit)
            if coords is None:
                continue
            board.add_unit(unit, coords[0], coords[1])

        return game
