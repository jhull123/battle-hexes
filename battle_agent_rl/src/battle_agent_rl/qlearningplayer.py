from pydantic import PrivateAttr
from typing import List

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction

from .rlplayer import RLPlayer


class QLearningPlayer(RLPlayer):
    """Simple Q-learning agent."""

    _alpha: float = PrivateAttr()
    _gamma: float = PrivateAttr()
    _epsilon: float = PrivateAttr()

    def __init__(
        self,
        name: str,
        type: PlayerType,
        factions: List[Faction],
        board: Board,
        alpha: float = 0.1,
        gamma: float = 0.9,
        epsilon: float = 0.1,
    ) -> None:
        super().__init__(name=name, type=type, factions=factions, board=board)
        self._alpha = alpha
        self._gamma = gamma
        self._epsilon = epsilon

    def movement(self) -> List[UnitMovementPlan]:
        # TODO: Implement movement logic for Q-learning player
        plans: List[UnitMovementPlan] = []
        return plans

    def combat_results(self, combat_results: CombatResults) -> None:
        """Informs the player of the combat results."""
        # TODO not implemented yet!
        pass

    def calculate_reward(self):
        """Return a positional reward for the current board state."""
        board = self._board
        friendly_units = self.own_units(board.get_units())
        enemy_units = [u for u in board.get_units() if u not in friendly_units]

        reward = 0.0
        for f_unit in friendly_units:
            friendly_strength = f_unit.get_attack() + f_unit.get_defense()
            f_hex = board.get_hex(f_unit.row, f_unit.column)
            for e_unit in enemy_units:
                enemy_strength = e_unit.get_attack() + e_unit.get_defense()
                e_hex = board.get_hex(e_unit.row, e_unit.column)
                distance = Board.hex_distance(f_hex, e_hex)
                if distance > 0:
                    reward += (friendly_strength - enemy_strength) / distance

        return reward
