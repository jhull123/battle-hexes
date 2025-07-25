from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, Hashable, List, Tuple

from pydantic import PrivateAttr

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction

from .rlplayer import RLPlayer


class QLearningPlayerOld(RLPlayer):
    """Old reference implementation for a simple tabular Q-learning agent."""

    _alpha: float = PrivateAttr()
    _gamma: float = PrivateAttr()
    _epsilon: float = PrivateAttr()
    _q: Dict[Tuple[Hashable, Hashable], float] = PrivateAttr()
    _last_actions: Dict[str, Tuple[Hashable, Hashable]] = PrivateAttr()

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
        self._q = defaultdict(float)
        self._last_actions = {}

    # ------------------------------------------------------------------
    # Q-Learning helpers
    # ------------------------------------------------------------------
    def choose_action(
        self, state: Hashable, actions: List[Hashable]
    ) -> Hashable:
        """Return an action using an \u03b5-greedy policy."""
        if not actions:
            return None
        if random.random() < self._epsilon:
            return random.choice(actions)
        q_values = [self._q[(state, a)] for a in actions]
        max_q = max(q_values)
        best_actions = [a for a, qv in zip(actions, q_values) if qv == max_q]
        return random.choice(best_actions)

    def update_q(
        self,
        state: Hashable,
        action: Hashable,
        reward: float,
        next_state: Hashable,
        next_actions: List[Hashable] | None = None,
    ) -> None:
        """Update Q-value using the tabular Q-learning rule."""
        if next_actions is None:
            next_values = [
                qv
                for (s, _), qv in self._q.items()
                if s == next_state
            ]
        else:
            next_values = [self._q[(next_state, a)] for a in next_actions]
        next_max = max(next_values) if next_values else 0.0
        old_q = self._q[(state, action)]
        self._q[(state, action)] = old_q + self._alpha * (
            reward + self._gamma * next_max - old_q
        )

    @property
    def q_table(self) -> Dict[Tuple[Hashable, Hashable], float]:
        return self._q

    # ------------------------------------------------------------------
    # Reward helpers
    # ------------------------------------------------------------------
    def calculate_reward(self, combat_results: CombatResults) -> int:
        """Return reward based on combat outcomes."""
        from battle_hexes_core.combat.combatresult import CombatResult

        attacker = bool(self._last_actions)
        reward = 0
        for battle in combat_results.get_battles():
            result = battle.get_combat_result()
            if result == CombatResult.DEFENDER_ELIMINATED:
                reward += 1 if attacker else -1
            elif result == CombatResult.ATTACKER_ELIMINATED:
                reward += -1 if attacker else 1
            elif result == CombatResult.EXCHANGE:
                # Both sides lose one unit
                reward += 0
        return reward

    # ------------------------------------------------------------------
    # Movement (\u03b5-greedy using Q-table). State is board snapshot.
    # ------------------------------------------------------------------
    _board: Board = PrivateAttr()

    def board_state(self) -> Tuple[Tuple[str, int, int], ...]:
        """Serialize board units into a hashable state tuple."""
        units = sorted(
            self._board.get_units(), key=lambda u: str(u.get_id())
        )
        return tuple((str(u.get_id()), u.row, u.column) for u in units)

    def movement(self) -> List[UnitMovementPlan]:
        plans: List[UnitMovementPlan] = []
        state = self.board_state()
        self._last_actions = {}
        for unit in self.own_units(self._board.get_units()):
            start_hex = self._board.get_hex(unit.row, unit.column)
            reachable = list(self._board.get_reachable_hexes(unit, start_hex))
            actions = [
                (unit.get_id(), h.row, h.column)
                for h in reachable
            ]
            chosen = self.choose_action(state, actions)
            if chosen is None:
                continue
            self._last_actions[str(unit.get_id())] = (state, chosen)
            _, row, col = chosen
            target_hex = self._board.get_hex(row, col)
            path = self._board.shortest_path(unit, start_hex, target_hex)
            if path:
                plans.append(UnitMovementPlan(unit, path))
        print("Raw Q-values current board state:")
        print(self.board_state)
        return plans

    def combat_results(self, combat_results: CombatResults) -> None:
        """Informs the player of the combat results."""
        reward = self.calculate_reward(combat_results)
        print("The reward for combat is:", reward)
        next_state = self.board_state()
        for state, action in self._last_actions.values():
            self.update_q(state, action, reward, next_state)
        self._last_actions = {}
        print("Q-table after combat:")
        print(self._format_q_table(next_state))
        print("Raw Q-values for next state:")
        print(next_state)

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------
    def _format_q_table(self, state: Hashable) -> str:
        """Return a human-readable Q-table for the given board state."""
        rows = []
        for r in range(self._board.get_rows()):
            indent = " " if r % 2 == 1 else ""
            cells = []
            for c in range(self._board.get_columns()):
                q_vals = [
                    self._q[(s, a)]
                    for (s, a) in self._q
                    if (
                        s == state
                        and isinstance(a, tuple)
                        and a[1] == r
                        and a[2] == c
                    )
                ]
                cell = f"{max(q_vals):4.1f}" if q_vals else "   ."
                cells.append(cell)
            rows.append(indent + " ".join(cells))
        return "\n".join(rows)
