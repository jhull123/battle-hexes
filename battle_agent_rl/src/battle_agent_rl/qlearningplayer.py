from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, Hashable, List, Tuple

from pydantic import PrivateAttr

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .rlplayer import RLPlayer


class QLearningPlayer(RLPlayer):
    """Simple tabular Q-learning agent."""

    _alpha: float = PrivateAttr()
    _gamma: float = PrivateAttr()
    _epsilon: float = PrivateAttr()
    _q: Dict[Tuple[Hashable, Hashable], float] = PrivateAttr()

    def __init__(
        self,
        name: str,
        type,
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
    # TODO this should be handled by combat_results()
    def elimination_reward(
        self,
        before_units: List[Unit],
        after_units: List[Unit],
    ) -> int:
        """Return reward for units eliminated between two board states."""
        friend_ids_before = {
            u.get_id()
            for u in before_units
            if u.get_faction() in self.factions
        }
        friend_ids_after = {
            u.get_id()
            for u in after_units
            if u.get_faction() in self.factions
        }
        enemy_ids_before = {
            u.get_id()
            for u in before_units
            if u.get_faction() not in self.factions
        }
        enemy_ids_after = {
            u.get_id()
            for u in after_units
            if u.get_faction() not in self.factions
        }
        friends_lost = len(friend_ids_before - friend_ids_after)
        enemies_eliminated = len(enemy_ids_before - enemy_ids_after)
        return enemies_eliminated - friends_lost

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
            _, row, col = chosen
            target_hex = self._board.get_hex(row, col)
            path = self._board.shortest_path(unit, start_hex, target_hex)
            if path:
                plans.append(UnitMovementPlan(unit, path))
        return plans

    def combat_results(self, combat_results: CombatResults) -> None:
        """Informs the player of the combat results."""
        # TODO !
        # This method can be used to update Q-values based on combat outcomes.
        pass
