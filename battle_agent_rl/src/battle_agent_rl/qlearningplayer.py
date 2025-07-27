from enum import Enum
from pydantic import PrivateAttr
from typing import List, Tuple
import uuid

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .rlplayer import RLPlayer


class ActionIntent(Enum):
    ADVANCE = "ADVANCE"
    RETREAT = "RETREAT"
    HOLD = "HOLD"


class QLearningPlayer(RLPlayer):
    """
    Simple Q-learning agent.

    _last_actions
    Temporary store for the most recent (state, action) pairs, used for Q-value
    updates.
    key: unit ID
    value:
        (my_strength, nearest_enemy_strength, distance_to_nearest_enemy),
        (action, magnitude)

    actions ∈ { "ADVANCE", "RETREAT", "HOLD" }
    magnitude ∈ { 0, 1, 2, ..., unit.get_move() }

    _q_table
    Q-value table that maps each (state, action) pair to a learned value
    estimate.
    key: Tuple[
        state: Tuple[int, int, int],
        action: Tuple[ActionIntent, int]
    ]
    value: float  # Estimated Q-value for taking that action in that state

    This table is updated using the standard Q-learning rule:
        Q(s, a) ← Q(s, a) + α * [r + γ * max_a' Q(s', a') - Q(s, a)]
    """

    _alpha: float = PrivateAttr()
    _gamma: float = PrivateAttr()
    _epsilon: float = PrivateAttr()

    _last_actions: dict = PrivateAttr()
    _q_table: dict = PrivateAttr()

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
        self._q_table = {}

    def movement(self) -> List[UnitMovementPlan]:
        self._last_actions = dict[uuid.UUID, Tuple]()
        for unit in self._board.get_units():
            state = self.encode_unit_state(unit)
            self._last_actions[unit.get_id()] = state
            print(unit.get_id(), "→", state)

        # TODO: Finish movement logic for Q-learning player

        plans: List[UnitMovementPlan] = []
        return plans

    def encode_unit_state(self, unit: Unit) -> Tuple[int, int, int]:
        """
        Encode the state for a given unit as:
        (my_strength, nearest_enemy_strength, distance_to_nearest_enemy)
        """
        board = self._board
        my_strength = unit.get_attack() + unit.get_defense()
        my_coords = unit.get_coords()

        if my_coords is None:
            return (my_strength, 0, 0)

        my_hex = board.get_hex(*my_coords)
        nearest_enemy = board.get_nearest_enemy_unit(unit)

        if nearest_enemy is None or nearest_enemy.get_coords() is None:
            return (my_strength, 0, 0)

        nearest_enemy_strength = (
            nearest_enemy.get_attack() + nearest_enemy.get_defense()
        )
        enemy_hex = board.get_hex(*nearest_enemy.get_coords())

        distance = Board.hex_distance(my_hex, enemy_hex)

        return (my_strength, nearest_enemy_strength, distance)

    def movement_cb(self) -> None:
        """
        Called after the player's unit plan has been applied to the board.
        """
        self.calculate_reward()

    def combat_results(self, combat_results: CombatResults) -> None:
        """
        Informs the player of the combat results.
        The board object is also updated at this point with the results of the
        player's movement plan.
        """
        # TODO update last actions based on combat results
        # TODO not implemented yet!
        pass

    def calculate_reward(self) -> float:
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

        print(f"Reward for {self.name}: {reward}")
        return reward
