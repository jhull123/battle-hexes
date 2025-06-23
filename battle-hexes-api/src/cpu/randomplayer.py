from random import choice
from typing import List, Set
from src.game.board import Board
from src.game.hex import Hex
from src.game.player import Player
from src.game.unitmovementplan import UnitMovementPlan


class RandomPlayer:
    def __init__(self,
                 player: Player,
                 board: Board):
        self.player = player
        self.board = board

    def movement(self) -> List[UnitMovementPlan]:
        plans = []
        for unit in self.player.own_units(self.board.get_units()):
            starting_hex = self.board.get_hex(unit.row, unit.column)
            reachable_hexes = self.board.get_reachable_hexes(
                unit,
                starting_hex
            )
            selected_hex = self.random_hex(reachable_hexes)
            print(
                f"Unit {unit.name} is moving from {starting_hex} to "
                f"{selected_hex}"
            )
            path = self.board.shortest_path(
                unit,
                starting_hex,
                selected_hex
            )
            if path:
                plans.append(UnitMovementPlan(unit, path))
        return plans

    def random_hex(self, hexes: Set[Hex]) -> Hex:
        """Select a random hex from the given set of hexes."""
        if not hexes:
            return None
        return choice(list(hexes))
