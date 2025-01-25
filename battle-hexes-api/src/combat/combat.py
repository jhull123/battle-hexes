from src.game.board import Board
from src.combat.combatresults import CombatResults


class Combat:
    def __init__(self, board: Board):
        self.board = board

    def resolve_combat(self):
        return CombatResults()
