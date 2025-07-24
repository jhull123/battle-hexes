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
        """
        Calculate the reward based on the player's unit positions on the board.

        TODO: Implement proximity-based reward to encourage strong units to
        move closer to weaker enemy units, and discourage approaching stronger
        enemies.

        For each pair of (friendly_unit, enemy_unit):

            1. Compute the strength of both units as:
               strength = unit.attack + unit.defense

            2. Compute the distance between the units using the board's hex
               distance:
               distance = board.hex_distance(friendly_hex, enemy_hex)

            3. If distance > 0, compute the pairwise reward as:
               (friendly_strength - enemy_strength) / distance

        Sum this value over all pairs of friendly and enemy units. This total
        value is the reward for the current board state.

        Notes:
        - This approach encourages a unit to move toward enemies it can likely
          defeat, and to stay away from stronger enemies.
        - Division by zero should be avoided; skip or guard against pairs at
          distance = 0.

        Consider:
        reward = self.calculate_reward()
        self.update_q(state, action, reward, next_state)

        You're telling your agent:

        “Taking this action from this state led to this reward and landed me
        in this next state.”

        This lets it learn which actions are worth repeating from similar board
        positions in the future.
        """
        pass
