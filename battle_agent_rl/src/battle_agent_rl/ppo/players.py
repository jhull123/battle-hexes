"""Core-compatible players for the single-unit training environment."""

from battle_hexes_core.game.player import Player
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan


class LearningPlayer(Player):
    def __post_init__(self):
        super().__post_init__()
        self.selected_plan = None

    def movement(self) -> list[UnitMovementPlan]:
        if self.selected_plan is None:
            raise RuntimeError(
                "Set a learning action before requesting movement"
            )
        plan = self.selected_plan
        self.selected_plan = None
        return [plan]

    def combat_results(self, combat_results):
        pass


class SeededRandomPlayer(RandomPlayer):
    """RandomPlayer movement with deterministic ordering and a local RNG."""

    def __init__(self, name, type, factions, board, rng):
        super().__init__(name, type, factions, board)
        self.rng = rng

    def random_hex(self, hexes):
        if not hexes:
            return None
        ordered = sorted(hexes, key=lambda tile: (tile.row, tile.column))
        return self.rng.choice(ordered)
