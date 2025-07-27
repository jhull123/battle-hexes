from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player
from battle_hexes_core.unit.unit import Unit


class GameFactory:
    def create_game(
            self,
            board_size: tuple[int, int],
            players: list[Player],
            units: list[Unit]
            ) -> Game:
        """Create a ``Game`` with the given board size, players and units."""
        rows, cols = board_size

        board = None
        for player in players:
            if hasattr(player, "_board"):
                board = getattr(player, "_board")
                break

        if (
            board is None
            or board.get_rows() != rows
            or board.get_columns() != cols
        ):
            board = Board(rows, cols)
            for player in players:
                if hasattr(player, "_board"):
                    player._board = board

        game = Game(players, board)

        for unit in units:
            coords = unit.get_coords()
            if coords is None:
                continue
            board.add_unit(unit, coords[0], coords[1])

        return game
