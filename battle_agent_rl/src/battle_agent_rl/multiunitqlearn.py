import logging
import math
from typing import List

from battle_hexes_core.game.board import Board
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction

from .rlplayer import RLPlayer

logger = logging.getLogger(__name__)


class MulitUnitQLearnPlayer(RLPlayer):
    """
    A Q-learning player for multi-unit battles.
    
    Unary state s_i  (order matters!)
    (my_str_bin, nearest_enemy_str_bin, dist_enemy_bin,
     nearest_ally_str_bin, dist_ally_bin, ally_density_bin)

    Pairwise state s_ij (symmetric; order matters only in the action pair)
     (ally_dist_bin, strength_ratio_bin, enemy_bearing_align_bin, local_crowding_bin)
    """

    def init(
        self,
        name: str,
        type: PlayerType,
        factions: List[Faction],
        board: Board
    ) -> None:
        super().__init__(name=name, type=type, factions=factions, board=board)


    def movement(self) -> List[UnitMovementPlan]:
        plans: List[UnitMovementPlan] = []
        for unit in self.own_units(self._board.get_units()):
            starting_hex = self._board.get_hex(unit.row, unit.column)
            plans.append(UnitMovementPlan(unit, [starting_hex]))
        return plans

    def _encode_unit_state(self, unit) -> tuple:
        """
        Returns a 6-tuple:
        (my_strength, nearest_enemy_strength, dist_to_enemy,
         nearest_ally_strength, dist_to_ally, ally_density_bin)
        """

        nearest_enemy = self._board.get_nearest_enemy_unit(unit)
        enemy_hex = self._board.get_hex(nearest_enemy.row, nearest_enemy.column)
        own_hex = self._board.get_hex(unit.row, unit.column)
        nearest_friend = self._board.get_nearest_friendly_unit(unit)
        friend_hex = self._board.get_hex(nearest_friend.row, nearest_friend.column)

        density = self._ally_density_decayed(unit, radius=8, use_exponential=False, lam=2.0)
        density_bin = self._bin_ally_density(density)

        return (
            unit.get_strength(),
            nearest_enemy.get_strength(),
            self._board.hex_distance(own_hex, enemy_hex),
            nearest_friend.get_strength(),
            self._board.hex_distance(own_hex, friend_hex),
            density_bin
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
                w = math.exp(-d / lam)         # smoother decay
            else:
                w = 1.0 / (1.0 + d)            # simple, fast

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
        if x <= 15.0: # heavy
            return 3
        return 4      # very heavy

    def movement_cb(self) -> None:
        """
        Called after the player's unit plan has been applied to the board.
        """
        for unit in self.own_units(self._board.get_units()):
            state = self._encode_unit_state(unit)
            logger.info(state)
