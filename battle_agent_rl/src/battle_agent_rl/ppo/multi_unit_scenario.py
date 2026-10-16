"""Fixed 9x9 prototype scenario and persistent unit slots."""

from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit


SLOTS = (
    ("learner-0", (3, 2)), ("learner-1", (5, 2)),
    ("opponent-0", (3, 6)), ("opponent-1", (5, 6)),
)


class PrototypePlayer(Player):
    """The local driver schedules orders; core callbacks do no bookkeeping."""

    def combat_results(self, combat_results):
        pass


def create_multi_unit_game(rng, learner_count=2, opponent_count=2):
    for count in (learner_count, opponent_count):
        if isinstance(count, bool) or not isinstance(count, int) \
                or count not in (1, 2):
            raise ValueError("Each side must have one or two units")
    board = Board(9, 9)
    learner = PrototypePlayer("Learner", PlayerType.CPU, [
        Faction("learner", "Learner", "blue")])
    opponent = PrototypePlayer("Opponent", PlayerType.CPU, [
        Faction("opponent", "Opponent", "red")])
    slots = [None] * 4
    for index, (unit_id, coords) in enumerate(SLOTS):
        if index % 2 >= (learner_count if index < 2 else opponent_count):
            continue
        player = learner if index < 2 else opponent
        unit = Unit(unit_id, unit_id.title(), player.factions[0], player,
                    "Infantry", 2, 2, 2)
        board.add_unit(unit, *coords)
        slots[index] = unit
    game = Game([learner, opponent], board, rng=rng)
    game.set_defensive_fire_settings(
        DefensiveFireSettings(base_probability=0.25))
    return game, learner, opponent, tuple(slots)
