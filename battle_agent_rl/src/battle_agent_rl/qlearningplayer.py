from enum import Enum
import logging
import math
import pickle
import random
from typing import Dict, List, Optional, Tuple

from pydantic import PrivateAttr

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.combat.combatresult import CombatResult
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


class ActionMagnitude(Enum):
    FULL = "FULL"
    HALF = "HALF"
    NONE = "NONE"


class QLearningPlayer(RLPlayer):
    """
    Simple Q-learning agent.
    """

    _alpha: float = PrivateAttr()
    _gamma: float = PrivateAttr()
    _epsilon: float = PrivateAttr()
    _turn_penalty: float = PrivateAttr()

    # Agent state attributes
    _turn_count: int = PrivateAttr()
    _last_actions: dict = PrivateAttr()
    _pair_last: dict = PrivateAttr()
    _q1: dict = PrivateAttr()         # unary table (s_i, a_i) -> float
    _q2: dict = PrivateAttr()         # pairwise tbl (s_ij, a_i, a_j) -> float

    _alpha_u: float = PrivateAttr()   # unary LR
    _alpha_p: float = PrivateAttr()   # pairwise LR
    _neighbor_radius: int = PrivateAttr()  # how far to search for allies
    _learn = PrivateAttr()
    _explore = PrivateAttr()

    def __init__(
        self,
        name: str,
        type: PlayerType,
        factions: List[Faction],
        board: Board,
        alpha: float = 0.09,
        gamma: float = 0.15,
        epsilon: float = 0.1,
        turn_penalty: float = 0.1,
    ) -> None:
        """
        Initialize a (Q-learning) player.

            Args:
            name (str): Human-readable name for the player (used in logs/UI).
            type (PlayerType): What kind of player this is (e.g., HUMAN, AI).
            factions (List[Faction]): One or more factions this player
            controls.
            board (Board): The game board instance the player will interact
                with.
            alpha (float, optional): Learning rate ∈ [0, 1]. Higher values make
                new rewards overwrite prior estimates more aggressively.
            gamma (float, optional): Discount factor ∈ [0, 1] for future
                rewards. 0 emphasizes immediate rewards; values near 1 value
                long-term return. Default: 0.15.
            epsilon (float, optional): Exploration rate ∈ [0, 1] for ε-greedy
                action selection. With probability ε the agent explores (random
                action); with probability 1−ε it exploits the best known
                action. Default: 0.1.
            turn_penalty (float, optional): Per-turn negative reward applied to
                discourage stalling and incentivize faster resolution.
                Typically a small positive number that is subtracted each turn.
                Default: 0.1.
        """

        super().__init__(name=name, type=type, factions=factions, board=board)
        self._alpha = alpha
        self._gamma = gamma
        self._epsilon = epsilon
        self._turn_penalty = turn_penalty
        self._turn_count = 0
        self._pair_last = {}
        self._last_actions = {}
        self._learn = True
        self._explore = True

        # pairwise Q-learning parameters
        self._q1 = {}
        self._q2 = {}
        self._alpha_u = alpha
        self._alpha_p = alpha * 0.25
        self._neighbor_radius = 12

    def disable_learning(self) -> None:
        """Disable learning for the agent."""
        self._learn = False
        self._alpha = 0.0

    def disable_exploration(self) -> None:
        """Disable exploration for the agent."""
        self._explore = False
        self._epsilon = 0.0

    def save_q_tables(self, file_path: str) -> None:
        with open(file_path, "wb") as f:
            pickle.dump({"Q1": self._q1, "Q2": self._q2}, f)

    def load_q_tables(self, file_path: str) -> None:
        with open(file_path, "rb") as f:
            data = pickle.load(f)
            self._q1 = data["Q1"]
            self._q2 = data["Q2"]

    # ----- Q1/Q2 getters -----
    def _q1_get(self, s_i, a_i) -> float:
        return self._q1.get((s_i, a_i), 0.0)

    def _q1_add(self, s_i, a_i, delta: float) -> None:
        key = (s_i, a_i)
        self._q1[key] = self._q1.get(key, 0.0) + delta

    def _q2_get(self, s_ij, a_i, a_j) -> float:
        return self._q2.get((s_ij, a_i, a_j), 0.0)

    def _q2_add(self, s_ij, a_i, a_j, delta: float) -> None:
        key = (s_ij, a_i, a_j)
        self._q2[key] = self._q2.get(key, 0.0) + delta

    def _canon_pair_key(self, s_ij, a_i, a_j):
        """Canonicalize pairwise state/action triple by arrival order."""

        eta_gap, power_bin = s_ij
        if eta_gap < 0:
            return ((-eta_gap, power_bin), a_j, a_i)
        return ((eta_gap, power_bin), a_i, a_j)

    def _select_actions_pairwise(
        self, units: List[Unit]
    ) -> Dict[Unit, Tuple[ActionIntent, ActionMagnitude]]:
        """
        Select joint actions via nearest-ally Q: ε-greedy on Q1, then one-sweep
        best response using Q1+Q2.
        """

        board = self._board
        unary_states: Dict[Unit, Tuple[int, ...]] = {}
        allies: Dict[Unit, Optional[Unit]] = {}
        pair_states: Dict[Unit, Tuple[int, int]] = {}
        action_lists: Dict[
            Unit, List[Tuple[ActionIntent, ActionMagnitude]]
        ] = {}

        # Precompute unary states, nearest allies, pair states, action lists
        for unit in units:
            unary_states[unit] = self.encode_unit_state(unit)
            allies[unit] = None
            pair_states[unit] = (0, 0)
            action_lists[unit] = self.available_actions(unit)

        # Link unit to nearest ally in range and cache pairwise state
        for unit in units:
            ally = board.get_nearest_friendly_unit(unit)
            if ally is None or ally is unit or ally not in unary_states:
                continue
            coords = unit.get_coords()
            ally_coords = ally.get_coords()
            if coords is None or ally_coords is None:
                continue
            unit_hex = board.get_hex(*coords)
            ally_hex = board.get_hex(*ally_coords)
            if unit_hex is None or ally_hex is None:
                continue
            distance = Board.hex_distance(unit_hex, ally_hex)
            if distance is None or distance > self._neighbor_radius:
                continue
            allies[unit] = ally
            pair_states[unit] = self._encode_pair_state(unit, ally)

        # Init per-unit actions: ε-greedy on Q1 (random or best unary action)
        joint_actions: Dict[Unit, Tuple[ActionIntent, ActionMagnitude]] = {}
        for unit in units:
            acts = action_lists[unit]
            if self._explore and random.random() < self._epsilon:
                joint_actions[unit] = random.choice(acts)
            else:
                qvals = [
                    (self._q1_get(unary_states[unit], action), action)
                    for action in acts
                ]
                joint_actions[unit] = max(qvals, key=lambda t: t[0])[1]

        # One-sweep best response: refine action using Q1+Q2 vs ally's action
        lambda_q2 = 0.2
        for unit in units:
            current = joint_actions[unit]
            s_ij = pair_states[unit]
            best_value = self._q1_get(unary_states[unit], current)
            ally = allies[unit]
            if ally is not None:
                (s_ij_c, ai_c, aj_c) = self._canon_pair_key(
                    s_ij, current, joint_actions[ally]
                )
                # Add the pairwise coordination value from _q2 to best_value
                best_value += lambda_q2 * self._q2_get(s_ij_c, ai_c, aj_c)
            # Score each candidate Q1+Q2 and keep the highest-scoring action
            for candidate in action_lists[unit]:
                value = self._q1_get(unary_states[unit], candidate)
                if ally is not None:
                    (s_ij_c, ai_c, aj_c) = self._canon_pair_key(
                        s_ij, candidate, joint_actions[ally]
                    )
                    value += lambda_q2 * self._q2_get(s_ij_c, ai_c, aj_c)
                if value > best_value:
                    best_value = value
                    current = candidate
            joint_actions[unit] = current

        return joint_actions

    def movement(self) -> List[UnitMovementPlan]:
        """
        Select pairwise-aware actions, snapshot pair states, and build
        UnitMovementPlans for all friendly units.
        """

        logger.info("")
        logger.info("")
        self._last_actions = {}
        plans: List[UnitMovementPlan] = []
        units = self.own_units(self._board.get_units())
        joint_actions = self._select_actions_pairwise(units)
        self._pair_last = {}

        # Snapshot in-range ally pair-state (s_ij) for learning updates
        for u in units:
            ally = self._board.get_nearest_friendly_unit(u)
            if (
                not ally
                or ally is u
                or ally.get_coords() is None
                or u.get_coords() is None
            ):
                continue
            u_hex = self._board.get_hex(*u.get_coords())
            a_hex = self._board.get_hex(*ally.get_coords())
            if not u_hex or not a_hex:
                continue
            d = Board.hex_distance(u_hex, a_hex)
            if d is None or d > self._neighbor_radius:
                continue
            s_ij = self._encode_pair_state(u, ally)
            self._pair_last[u.get_id()] = (ally.get_id(), s_ij)

        # Store state/action, create movement plan, append to plans
        for unit in units:
            state = self.encode_unit_state(unit)
            chosen = joint_actions[unit]
            self._last_actions[unit.get_id()] = (unit, state, chosen)
            plan = self.move_plan(unit, chosen[0], chosen[1])
            if plan is not None:
                plans.append(plan)

        logging.info("\nAgent state after movement...")
        self.print_agent_state(logging.INFO)
        logging.info("")
        return plans

    def _encode_pair_state(self, ui: Unit, uj: Unit) -> tuple[int, int]:
        """
        Returns a 2-tuple describing the pair (ui, uj) anchored on ui's nearest
        enemy:

        - eta_diff_bin: ETA gap to ui’s nearest enemy, binned to
            {-2,-1,0,+1,+2}. eta_diff_bin = clamp_[-2,+2](ETA(uj→E_ui)
            - ETA(ui→E_ui)) where
            ETA(x→E_ui) is the additional turns (0..3, with 3 = "3+ turns") for
            unit x to reach E_ui given its move factor.
            Interpretation: 0 = arrive same turn, 1 = ally lags by 1 turn,
            2 = ally lags by ≥2 turns. Negative values mean the ally arrives
            earlier; callers canonicalize on use.

        - power_diff_bin: normalized power advantage of (ui+uj) vs E_ui,
            i.e., ((str_ui + str_uj) - str_enemy) / max(1, str_enemy),
            binned to {-2,-1,0,+1,+2}.
        """
        board = self._board

        # If any units lack coordinates we cannot compute distances/ETAs.
        if ui.get_coords() is None or uj.get_coords() is None:
            return (0, 0)

        # Find the enemy unit closest to ui. Pairwise state is anchored on
        # this enemy. If no enemy exists we return a neutral state.
        enemy = board.get_nearest_enemy_unit(ui)
        if enemy is None or enemy.get_coords() is None:
            return (0, 0)

        ui_hex = board.get_hex(*ui.get_coords())
        uj_hex = board.get_hex(*uj.get_coords())
        enemy_hex = board.get_hex(*enemy.get_coords())
        if ui_hex is None or uj_hex is None or enemy_hex is None:
            return (0, 0)

        # --- ETA difference bin ---
        dist_ui = Board.hex_distance(ui_hex, enemy_hex)
        dist_uj = Board.hex_distance(uj_hex, enemy_hex)
        eta_ui = self._distance_to_eta_bin(dist_ui, ui.get_move())
        eta_uj = self._distance_to_eta_bin(dist_uj, uj.get_move())
        eta_gap = eta_uj - eta_ui               # + => uj lags, - => uj leads
        eta_gap_bin = max(-2, min(2, eta_gap))  # [-2..+2], keeps direction

        # --- Power advantage bin ---
        str_enemy = enemy.get_strength()
        power_diff = (
            (ui.get_strength() + uj.get_strength()) - str_enemy
        ) / max(1, str_enemy)

        # Round to nearest int, breaking .5 ties away from zero, then clamp.
        if power_diff >= 0:
            power_diff_bin = int(math.floor(power_diff + 0.5))
        else:
            power_diff_bin = int(-math.floor(-power_diff + 0.5))
        power_diff_bin = max(-2, min(2, power_diff_bin))

        return (eta_gap_bin, power_diff_bin)

    def move_plan(
            self,
            unit: Unit,
            action: ActionIntent,
            magnitude: ActionMagnitude
            ) -> UnitMovementPlan:
        """
        Create a movement plan for the unit based on the chosen action and
        magnitude.

        ``ADVANCE``: move toward the nearest enemy hex.
        ``RETREAT``: move away from the nearest enemy hex.
        ``HOLD``: do not move.

        ``FULL`` uses all movement points, ``HALF`` uses half (floored) and
        ``NONE`` results in no movement.
        """
        board = self._board
        start_coords = unit.get_coords()
        if start_coords is None:
            return UnitMovementPlan(unit, [])

        start_hex = board.get_hex(*start_coords)
        if start_hex is None:
            return UnitMovementPlan(unit, [])

        move_points = unit.get_move()
        if magnitude == ActionMagnitude.HALF:
            move_points = move_points // 2
        elif magnitude == ActionMagnitude.NONE:
            move_points = 0

        if action == ActionIntent.HOLD or move_points <= 0:
            return UnitMovementPlan(unit, [start_hex])

        enemy = board.get_nearest_enemy_unit(unit)
        if enemy is None or enemy.get_coords() is None:
            return UnitMovementPlan(unit, [start_hex])

        enemy_hex = board.get_hex(*enemy.get_coords())

        if action == ActionIntent.ADVANCE:
            path = board.path_towards(unit, enemy_hex, move_points)
        else:  # RETREAT
            path = board.path_away_from(unit, enemy_hex, move_points)

        if not path:
            path = [start_hex]

        return UnitMovementPlan(unit, path)

    def available_actions(
        self, unit: Unit
    ) -> List[Tuple[ActionIntent, ActionMagnitude]]:
        actions = [(ActionIntent.HOLD, ActionMagnitude.NONE)]
        move = unit.get_move()
        if move > 0:
            actions.append((ActionIntent.ADVANCE, ActionMagnitude.HALF))
            actions.append((ActionIntent.ADVANCE, ActionMagnitude.FULL))
            actions.append((ActionIntent.RETREAT, ActionMagnitude.HALF))
            actions.append((ActionIntent.RETREAT, ActionMagnitude.FULL))
        return actions

    def update_q(
        self,
        unit: Unit,
        state: Tuple[int, int, int, int, int, int],
        action: Tuple[ActionIntent, ActionMagnitude],
        reward: float,
        next_state: Tuple[int, int, int, int, int, int],
        next_actions: List[Tuple[ActionIntent, ActionMagnitude]],
    ) -> None:
        """
        TD update for factored Q: bootstrap from max Q1(s′,·); update Q1(s,a)
        and Q2(s_ij,a,a_ally) using pre-move ally snapshot.
        """

        if not self._learn:
            return

        # --- Bootstrap using Q1 only (simple, stable) ---
        q1_now = self._q1_get(state, action)
        if next_actions:
            next_max_q1 = max(
                self._q1_get(next_state, a) for a in next_actions
            )
        else:
            next_max_q1 = 0.0

        td = reward + self._gamma * next_max_q1 - q1_now

        # Update unary table
        self._q1_add(state, action, self._alpha_u * td)

        # --- Update pairwise table using pre-move snapshot (if available) ---
        pair = self._pair_last.get(unit.get_id())
        if pair:
            ally_id, s_ij = pair
            ally_rec = self._last_actions.get(ally_id)
            if ally_rec:
                ally_action = ally_rec[2]  # (ActionIntent, ActionMagnitude)
                (s_ij_c, ai_c, aj_c) = self._canon_pair_key(
                    s_ij, action, ally_action
                )
                if unit.get_id() < ally_id:  # update each pair once
                    self._q2_add(s_ij_c, ai_c, aj_c, self._alpha_p * td)

    def _distance_to_eta_bin(self, distance: int, move: int) -> int:
        """Convert a hex distance to an ETA bin based on ``move``.

        The result is the number of additional turns required to reach the
        target hex, clamped to ``0``--``3``. Distances of zero or units with no
        movement return ``0``.
        """
        if distance <= 0 or move <= 0:
            return 0
        extra_turns = (distance - 1) // move
        return min(3, extra_turns)

    def encode_unit_state(
            self, unit: Unit
    ) -> Tuple[int, int, int, int, int, int]:
        """Return a 6-tuple state for ``unit``.

        ``(my_strength, nearest_enemy_strength, eta_to_enemy,
         nearest_ally_strength, eta_ally_to_enemy, ally_density_bin)``

        ``eta_to_enemy`` is the number of additional turns (0--3) the
        unit would need to reach its nearest enemy based on the unit's
        movement factor. ``eta_ally_to_enemy`` uses the nearest ally's
        movement factor to estimate the turns required for that ally to
        reach the unit's nearest enemy.
        """

        my_strength = unit.get_strength()
        coords = unit.get_coords()
        if coords is None:
            return (my_strength, 0, 0, 0, 0, 0)

        own_hex = self._board.get_hex(*coords)
        if own_hex is None:
            return (my_strength, 0, 0, 0, 0, 0)

        move = unit.get_move()

        nearest_enemy = self._board.get_nearest_enemy_unit(unit)
        enemy_hex = None
        if nearest_enemy is None or nearest_enemy.get_coords() is None:
            enemy_strength = 0
            enemy_eta = 0
        else:
            enemy_hex = self._board.get_hex(*nearest_enemy.get_coords())
            enemy_strength = nearest_enemy.get_strength()
            enemy_dist = Board.hex_distance(own_hex, enemy_hex)
            enemy_eta = self._distance_to_eta_bin(enemy_dist, move)

        nearest_friend = self._board.get_nearest_friendly_unit(unit)
        if nearest_friend is None or nearest_friend.get_coords() is None:
            friend_strength = 0
            friend_eta = 0
        else:
            friend_strength = nearest_friend.get_strength()
            if enemy_hex is None:
                friend_eta = 0
            else:
                friend_hex = self._board.get_hex(*nearest_friend.get_coords())
                friend_dist = Board.hex_distance(friend_hex, enemy_hex)
                friend_eta = self._distance_to_eta_bin(
                    friend_dist, nearest_friend.get_move()
                )

        density = self._ally_density_decayed(
            unit, radius=8, use_exponential=False, lam=2.0
        )
        density_bin = self._bin_ally_density(density)

        return (
            my_strength,
            enemy_strength,
            enemy_eta,
            friend_strength,
            friend_eta,
            density_bin,
        )

    def _ally_density_decayed(
        self,
        unit,
        radius: int = 2,
        use_exponential: bool = False,
        lam: float = 2.0,
    ) -> float:
        """
        Sum over friendly units within `radius` of weight(d) * strength,
        where weight(d) = 1/(1+d)  (or exp(-d/lam) if use_exponential=True).
        Excludes `unit` itself.
        """
        me_hex = self._board.get_hex(unit.row, unit.column)
        total = 0.0

        for f in self.own_units(self._board.get_units()):
            if f is unit:
                continue
            f_hex = self._board.get_hex(f.row, f.column)
            d = Board.hex_distance(me_hex, f_hex)
            if d is None or d > radius:
                continue

            if use_exponential:
                w = math.exp(-d / lam)  # smoother decay
            else:
                w = 1.0 / (1.0 + d)  # simple, fast

            # if your Unit lacks get_strength(), swap for f.strength
            total += w * float(f.get_strength())

        return total

    def _bin_ally_density(self, x: float) -> int:
        """
        Coarse bins so the tabular Q doesn't explode.
        Tune thresholds after logging a few hundred values.
        """
        if x <= 0.0:  # none
            return 0
        if x <= 4.0:  # light
            return 1
        if x <= 9.0:  # medium
            return 2
        if x <= 15.0:  # heavy
            return 3
        return 4  # very heavy

    def movement_cb(self) -> None:
        """
        Called after the player's unit plan has been applied to the board.
        """
        self._turn_count += 1
        reward = (
            # self.calculate_reward() - self._turn_penalty * self._turn_count
            self._turn_count * -0.1
        )
        for unit, state_action in [
            (record[0], (record[1], record[2]))
            for record in self._last_actions.values()
        ]:
            state, action = state_action
            next_state = self.encode_unit_state(unit)
            next_actions = self.available_actions(unit)
            self.update_q(
                unit, state, action, reward, next_state, next_actions
            )
        # Do not clear _last_actions here so combat_results can also use them
        logging.info("\nAgent state after movement callback...")
        self.print_agent_state(logging.INFO)
        logging.info("")

    def combat_results(self, combat_results: CombatResults) -> None:
        """
        Informs the player of the combat results.
        The board object is also updated at this point with the results of the
        player's movement plan.
        """
        attacker = bool(self._last_actions)
        bonus = 100.0
        half_bonus = bonus / 2.0
        double_bonus = bonus * 2.0

        reward = 0.0
        for battle in combat_results.get_battles():
            combat_award = 0.0
            match battle.get_odds():
                case (1, 7) | (1, 6) | (1, 5) | (1, 4) | (1, 3):
                    combat_award = -bonus
                case (1, 2):
                    combat_award = -half_bonus
                case (1, 1):
                    combat_award = 0.0
                case (2, 1):
                    combat_award = bonus
                case (3, 1) | (4, 1) | (5, 1) | (6, 1) | (7, 1):
                    combat_award = double_bonus

            result = battle.get_combat_result()
            # results bonus
            if result == CombatResult.EXCHANGE:
                combat_award -= half_bonus
            elif result == CombatResult.ATTACKER_ELIMINATED:
                combat_award += -half_bonus if attacker else half_bonus
            # elif result == CombatResult.DEFENDER_ELIMINATED:
            #     combat_award += double_bonus if attacker else -half_bonus
            # else:
            #     combat_award += half_bonus if attacker else 1.0
            logger.info(
                "Combat award is %s for %s at %s odds",
                combat_award, result, battle.get_odds()
            )
            reward += combat_award

        for unit, state_action in [
            (record[0], (record[1], record[2]))
            for record in self._last_actions.values()
        ]:
            state, action = state_action
            next_state = self.encode_unit_state(unit)
            next_actions = self.available_actions(unit)
            self.update_q(
                unit, state, action, reward, next_state, next_actions
            )

        logging.info("\nAgent state after combat results...")
        self.print_agent_state(logging.INFO)
        logging.info("")

        # Clear stored actions now that Q-values have been updated
        self._last_actions = {}
        self._pair_last = {}

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

        logger.info(f"Reward for {self.name}: {reward}")
        return reward

    def end_game_cb(self) -> None:
        """
        Called at the end of the game.
        """
        logger.info(
            "\nGame over for %s after %d turns.",
            self.name, self._turn_count
        )
        self.print_agent_state(logging.INFO)

    def print_agent_state(self, level: int = logging.INFO) -> None:
        """
        Print the agent's internal state for debugging purposes.

        A logging level may be passed (default: logging.INFO). The messages
        will be emitted using :py:meth:`logging.Logger.log` so callers can
        choose a different severity (e.g. DEBUG).
        """
        if not logger.isEnabledFor(level):
            return

        logger.log(level, "Agent state for %s:", self.name)
        logger.log(level, "  Turn count: %d", self._turn_count)

        logger.log(level, "  Last Actions [unit ID, (unit, state, action)]")
        for unit_id, action in self._last_actions.items():
            logger.log(level, f"    {unit_id}={action}")

        logger.log(level, "  Last Pair Actions [unit ID, (ally_id, s_ij)]")
        for unit_id, pair in self._pair_last.items():
            logger.log(level, f"    {unit_id}={pair}")

        logger.log(level, "  Q1 table [(s_i, a_i), q_value]")
        for (state, action), q_value in sorted(
            self._q1.items(), key=lambda item: item[1], reverse=True
        ):
            logger.log(level, f"    ({state}, {action}) = {q_value:.4f}")

        logger.log(level, "  Q2 table [(s_ij, a_i, a_j), q_value]")
        for (state, action_i, action_j), q_value in sorted(
            self._q2.items(), key=lambda item: item[1], reverse=True
        ):
            logger.log(
                level,
                f"    ({state}, {action_i}, {action_j}) = {q_value:.4f}"
            )
