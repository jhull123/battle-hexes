"""Read-only reinforcement menu schemas."""

from typing import Literal

from .api_model import ApiBaseModel


class ReinforcementUnitModel(ApiBaseModel):
    """A menu-ready unit waiting outside the board."""

    unit_id: str
    name: str
    faction_id: str
    attack: int
    defense: int
    movement: int
    entry_coordinate: tuple[int, int]


class PendingReinforcementModel(ApiBaseModel):
    """A reinforcement group that has not entered play."""

    arrival_turn: int
    status: Literal["scheduled", "delayed"]
    player_name: str
    units: list[ReinforcementUnitModel]


class ReinforcementsModel(ApiBaseModel):
    """Optional game-menu reinforcement payload."""

    pending: list[PendingReinforcementModel]

    @classmethod
    def from_game(cls, game):
        """Serialize the core's already-computed pending representation."""
        deployer = game.reinforcements_deployer
        if not deployer.groups:
            return None
        pending = []
        for group in deployer.pending(game.turn_number):
            pending.append(PendingReinforcementModel(
                arrival_turn=group.arrival_turn,
                status=group.status,
                player_name=group.units[0].player.name,
                units=[
                    ReinforcementUnitModel(
                        unit_id=unit.id,
                        name=unit.name,
                        faction_id=unit.faction.id,
                        attack=unit.attack,
                        defense=unit.defense,
                        movement=unit.move,
                        entry_coordinate=group.coords,
                    )
                    for unit in group.units
                ],
            ))
        return cls(pending=pending)
