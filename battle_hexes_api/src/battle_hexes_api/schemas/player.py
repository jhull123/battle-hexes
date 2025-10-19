"""Pydantic schema for player resources."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from battle_hexes_core.game.player import Player, PlayerType

from .faction import FactionModel


class PlayerModel(BaseModel):
    """Pydantic representation of a core :class:`Player`."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    type: str
    factions: list[FactionModel]

    @classmethod
    def from_core(cls, player: Player) -> "PlayerModel":
        """Create a ``PlayerModel`` from a core :class:`Player`."""

        player_type = (
            player.type.value
            if isinstance(player.type, PlayerType)
            else str(player.type)
        )
        return cls(
            name=player.name,
            type=player_type,
            factions=[
                FactionModel.from_core(faction)
                for faction in player.factions
            ],
        )

    def to_core(self) -> Player:
        """Convert the schema back into a core :class:`Player`."""

        factions = [faction.to_core() for faction in self.factions]

        if isinstance(self.type, PlayerType):
            player_type = self.type
        elif isinstance(self.type, str):
            try:
                player_type = PlayerType(self.type)
            except ValueError:
                try:
                    player_type = PlayerType[self.type]
                except KeyError as exc:
                    raise ValueError(
                        f"Unsupported player type value: {self.type!r}"
                    ) from exc
        else:
            raise TypeError(
                "PlayerModel.type must be a string or PlayerType instance"
            )

        return Player(name=self.name, type=player_type, factions=factions)
