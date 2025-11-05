from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List
from battle_hexes_core.combat.combatresults import CombatResults
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan


class PlayerType(Enum):
    HUMAN = "Human"
    CPU = "Computer"


@dataclass
class Player:
    name: str
    type: PlayerType
    factions: List[Faction] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Store factions as a concrete list to match the previous behaviour.
        self.factions = list(self.factions)

    def add_faction(self, faction: Faction) -> None:
        self.factions.append(faction)

    def has_faction(self, faction: Faction) -> bool:
        return faction in self.factions

    def owns(self, unit) -> bool:
        return unit.faction in self.factions

    def own_units(self, units: Iterable) -> List:
        return [unit for unit in units if self.owns(unit)]

    def movement(self) -> List[UnitMovementPlan]:
        """Return a list of movement plans for the player's units."""
        raise NotImplementedError("Subclasses must implement movement")

    def movement_cb(self) -> None:
        """
        Called after the player's unit plan has been applied to the board.
        """
        pass

    def combat_results(self, combat_results: CombatResults) -> None:
        """Informs the player of the combat results."""
        raise NotImplementedError("Subclasses must implement combat_results")

    def end_game_cb(self) -> None:
        """Called when the game has concluded."""
        pass
