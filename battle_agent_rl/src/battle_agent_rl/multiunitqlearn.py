import logging
import math
from typing import List, Tuple

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .qlearningplayer import QLearningPlayer

logger = logging.getLogger(__name__)


class MulitUnitQLearnPlayer(QLearningPlayer):
    """A Q-learning player for multi-unit battles.

    Unary state ``s_i`` (order matters!)
    ``(my_str_bin, nearest_enemy_str_bin, eta_enemy_bin,``
    `` nearest_ally_str_bin, eta_ally_bin, ally_density_bin)``
    ``eta_enemy_bin`` is the estimated additional turns (0--3) the unit
    would need to reach the nearest enemy based on its movement factor.
    ``eta_ally_bin`` measures the turns the nearest ally would need to
    reach that same enemy using the ally's movement factor.

    Pairwise state ``s_ij`` (symmetric; order matters only in the action
    pair)
    ``(ally_dist_bin, strength_ratio_bin, enemy_bearing_align_bin,``
    `` local_crowding_bin)``
    """

    def init(
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
        super().__init__(
            name=name, type=type, factions=factions, board=board, alpha=alpha,
            gamma=gamma, epsilon=epsilon, turn_penalty=turn_penalty
        )

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
            enemy_dist = self._board.hex_distance(own_hex, enemy_hex)
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
                friend_dist = self._board.hex_distance(friend_hex, enemy_hex)
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
            d = self._board.hex_distance(me_hex, f_hex)
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
