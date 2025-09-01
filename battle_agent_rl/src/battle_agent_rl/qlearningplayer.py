from enum import Enum
import logging
import pickle
import random
from typing import List, Tuple

from pydantic import PrivateAttr

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .rlplayer import RLPlayer


logger = logging.getLogger(__name__)


class ActionIntent(Enum):
    ADVANCE = "ADVANCE"
    RETREAT = "RETREAT"
    HOLD = "HOLD"


class QLearningPlayer(RLPlayer):
    """
    Simple Q-learning agent.

    _last_actions
    Temporary store for the most recent unit, state and action tuples used
    when updating Q-values after movement or combat.
    key: unit ID
    value:
        (unit, state, action)
            unit: Unit object reference
            state: (my_strength, nearest_enemy_strength, distance)
            action: (ActionIntent, magnitude)

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
    _turn_penalty: float = PrivateAttr()
    _turn_count: int = PrivateAttr()

    _last_actions: dict = PrivateAttr()
    _q_table: dict = PrivateAttr()

    def __init__(
        self,
        name: str,
        type: PlayerType,
        factions: List[Faction],
        board: Board,
        alpha: float = 0.1,
        gamma: float = 0.15,
        epsilon: float = 0.1,
        turn_penalty: float = 0.1,
    ) -> None:
        super().__init__(name=name, type=type, factions=factions, board=board)
        self._alpha = alpha
        self._gamma = gamma
        self._epsilon = epsilon
        self._turn_penalty = turn_penalty
        self._turn_count = 0
        self._q_table = {}
        self._last_actions = {}

    def save_q_table(self, file_path: str) -> None:
        """Save the internal Q-table to ``file_path`` using pickle."""
        with open(file_path, "wb") as f:
            pickle.dump(self._q_table, f)

    def load_q_table(self, file_path: str) -> None:
        """Load a Q-table from ``file_path`` if the file exists."""
        try:
            with open(file_path, "rb") as f:
                self._q_table = pickle.load(f)
        except FileNotFoundError:
            pass

    def movement(self) -> List[UnitMovementPlan]:
        self._last_actions = {}
        plans: List[UnitMovementPlan] = []
        for unit in self.own_units(self._board.get_units()):
            state = self.encode_unit_state(unit)
            actions = self.available_actions(unit)
            chosen = self.choose_action(state, actions)
            # Store the unit reference so we can update after combat even if it
            # was destroyed.
            self._last_actions[unit.get_id()] = (unit, state, chosen)
            plan = self.move_plan(unit, chosen[0], chosen[1])
            if plan is not None:
                plans.append(plan)

        # self.print_last_actions()
        return plans

    def move_plan(
            self,
            unit: Unit,
            action: ActionIntent,
            magnitude: int
            ) -> UnitMovementPlan:
        """
        Create a movement plan for the unit based on the chosen action and
        magnitude.
        ADVANCE: move toward the nearest enemy hex by the specified
                 magnitude.
        RETREAT: move away from the nearest enemy hex by the specified
                 magnitude.
        HOLD: do not move.
        """
        board = self._board
        start_coords = unit.get_coords()
        if start_coords is None:
            return UnitMovementPlan(unit, [])

        start_hex = board.get_hex(*start_coords)
        if start_hex is None:
            return UnitMovementPlan(unit, [])

        if action == ActionIntent.HOLD or magnitude <= 0:
            return UnitMovementPlan(unit, [start_hex])

        enemy = board.get_nearest_enemy_unit(unit)
        if enemy is None or enemy.get_coords() is None:
            return UnitMovementPlan(unit, [start_hex])

        enemy_hex = board.get_hex(*enemy.get_coords())

        if action == ActionIntent.ADVANCE:
            path = board.path_towards(unit, enemy_hex, magnitude)
        else:  # RETREAT
            path = board.path_away_from(unit, enemy_hex, magnitude)

        if not path:
            path = [start_hex]

        return UnitMovementPlan(unit, path)

    def available_actions(self, unit: Unit) -> List[Tuple[ActionIntent, int]]:
        actions = [(ActionIntent.HOLD, 0)]
        move = unit.get_move()
        for i in range(1, move + 1):
            actions.append((ActionIntent.ADVANCE, i))
            actions.append((ActionIntent.RETREAT, i))
        return actions

    def choose_action(
        self,
        state: Tuple[int, int, int],
        actions: List[Tuple[ActionIntent, int]],
    ) -> Tuple[ActionIntent, int]:
        if not actions:
            return (ActionIntent.HOLD, 0)
        if random.random() < self._epsilon:
            return random.choice(actions)

        # logger.info("Available actions are:")
        # for a in actions:
        #     logger.info("  Action: %s", a)

        q_values = [self._q_table.get((state, a), 0.0) for a in actions]

        # example_key = (state, (ActionIntent.HOLD, 0))
        # logger.info("Example key is: %s", example_key)

        # example_q = self._q_table.get(example_key)  # Example access to Q-val
        # logger.info("Example Q-value is: %s", example_q)

        logger.info("Current state is: %s", state)
        logger.info("Q-values are:")
        for a, q in zip(actions, q_values):
            if q != 0.0:
                logger.info("  Action: %s, Q-value: %.4f", a, q)

        max_q = max(q_values)
        best = [a for a, q in zip(actions, q_values) if q == max_q]

        # logger.info("Best actions are:")
        # for a in best:
        #     logger.info("  Action: %s", a)

        return random.choice(best)

    def update_q(
        self,
        state: Tuple[int, int, int],
        action: Tuple[ActionIntent, int],
        reward: float,
        next_state: Tuple[int, int, int],
        next_actions: List[Tuple[ActionIntent, int]],
    ) -> None:
        next_q_values = [
            self._q_table.get((next_state, a), 0.0) for a in next_actions
        ]
        next_max = max(next_q_values) if next_q_values else 0.0
        old_q = self._q_table.get((state, action), 0.0)
        self._q_table[(state, action)] = old_q + self._alpha * (
            reward + self._gamma * next_max - old_q
        )

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
        self._turn_count += 1
        reward = (
            self.calculate_reward() - self._turn_penalty * self._turn_count
        )
        for unit, state_action in [
            (record[0], (record[1], record[2]))
            for record in self._last_actions.values()
        ]:
            state, action = state_action
            next_state = self.encode_unit_state(unit)
            next_actions = self.available_actions(unit)
            self.update_q(state, action, reward, next_state, next_actions)
        # Do not clear _last_actions here so combat_results can also use them
        self.print_q_table(logging.DEBUG)

    def combat_results(self, combat_results: CombatResults) -> None:
        """
        Informs the player of the combat results.
        The board object is also updated at this point with the results of the
        player's movement plan.
        """
        from battle_hexes_core.combat.combatresult import CombatResult

        # Determine if this player was the attacker.
        # During the attacker's turn ``_last_actions`` stores the actions.
        attacker = bool(self._last_actions)
        bonus = 1000.0

        reward = 0.0
        for battle in combat_results.get_battles():
            result = battle.get_combat_result()
            combat_award = 0.0
            if result == CombatResult.DEFENDER_ELIMINATED:
                combat_award += bonus if attacker else -bonus
            elif result == CombatResult.ATTACKER_ELIMINATED:
                combat_award += -bonus if attacker else bonus
            elif result == CombatResult.EXCHANGE:
                combat_award += bonus * 0.10
            else:
                combat_award += bonus * 0.10
            logger.info("Combat award is %s for %s", combat_award, result)
            reward += combat_award

        for unit, state_action in [
            (record[0], (record[1], record[2]))
            for record in self._last_actions.values()
        ]:
            state, action = state_action
            next_state = self.encode_unit_state(unit)
            next_actions = self.available_actions(unit)
            self.update_q(state, action, reward, next_state, next_actions)

        # Clear stored actions now that Q-values have been updated
        self._last_actions = {}

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
                else:
                    logger.info(
                        "Warning: Distance is zero in calculate_reward!"
                    )

        # print(f"Reward for {self.name}: {reward}")
        return reward

    def end_game_cb(self) -> None:
        self.print_q_table()
        pass

    def print_last_actions(self) -> None:
        """Print the last actions taken by the player."""
        logger.info("Last actions for %s:", self.name)
        for unit_id, (unit, state, action) in self._last_actions.items():
            msg = (
                f"  Unit ID: {unit_id}, Unit: {unit.get_name()}, "
                f"State: {state}, Action: {action}"
            )
            logger.info(msg)

    def print_q_table(self, level: int = logging.INFO) -> None:
        """Print the Q-table for debugging purposes.

        A logging level may be passed (default: logging.INFO). The messages
        will be emitted using :py:meth:`logging.Logger.log` so callers can
        choose a different severity (e.g. DEBUG).
        """
        # Avoid expensive formatting/sorting when the logger won't emit at
        # the requested level.
        if not logger.isEnabledFor(level):
            return

        logger.log(level, "Q-table for %s:", self.name)
        items = sorted(
            self._q_table.items(), key=lambda item: item[1], reverse=True
        )
        for (state, action), value in items:
            logger.log(
                level, "  State: %s, Action: %s, Q-value: %.4f", state, action,
                value
            )
