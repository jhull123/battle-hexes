from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction


class HumanPlayer(Player):
    def __init__(
        self,
        name: str,
        factions: list[Faction],
        board: Board,
    ) -> None:
        super().__init__(name=name, type=PlayerType.HUMAN, factions=factions)
        self._board = board

    def movement(self):  # pragma: no cover
        """Human players plan movement client-side."""
        return []

    def combat_results(self, combat_results):  # pragma: no cover
        """Human players review combat results client-side."""
        return None
