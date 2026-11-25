"""Stateless scripted CPU policy for ordinary core turns."""

from dataclasses import dataclass, field

from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan


@dataclass
class ScriptedPlayer(Player):
    """Issue no movement orders and let the game resolve the usual phases."""

    type: PlayerType = field(default=PlayerType.CPU, init=False)

    def movement(self) -> list[UnitMovementPlan]:
        return []

    def combat_results(self, combat_results: CombatResults) -> None:
        pass
