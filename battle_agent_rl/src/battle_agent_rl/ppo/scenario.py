"""Construction and binding checks for the fixed checkpoint scenario."""

from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .players import SeededRandomPlayer


def create_game(learner, rng):
    """Build the exact 01–04 scenario with a shared opponent/combat RNG."""
    board = Board(5, 5)
    opponent = SeededRandomPlayer(
        "Opponent", PlayerType.CPU,
        [Faction("opponent", "Opponent", "red")], board, rng,
    )
    board.add_unit(Unit(
        "learner", "Learner", learner.factions[0], learner,
        "Infantry", 2, 2, 2,
    ), 2, 0)
    board.add_unit(Unit(
        "opponent", "Opponent", opponent.factions[0], opponent,
        "Infantry", 2, 2, 2,
    ), 2, 4)
    game = Game([learner, opponent], board, rng=rng)
    game.set_defensive_fire_settings(
        DefensiveFireSettings(base_probability=0.25)
    )
    return game


def validate_initial_game(game, learner):
    """Never apply the 5x5 model to a different initial ruleset."""
    board = game.get_board()
    players = game.get_players()
    if (len(players) != 2 or players[0] is not learner
            or game.get_current_player() is not learner
            or not isinstance(players[1], SeededRandomPlayer)
            or learner.type is not PlayerType.CPU
            or players[1].type is not PlayerType.CPU
            or len(learner.factions) != 1
            or len(players[1].factions) != 1
            or learner.factions[0].id != "learner"
            or players[1].factions[0].id != "opponent"
            or learner.name != "Learner" or players[1].name != "Opponent"):
        raise ValueError("Unsupported PPO player order, factions or opponent")
    validate_live_game(game, learner)
    units = board.get_units()
    if (len(units) != 2 or len(board.get_known_units()) != 2
            or not _unit_matches(units[0], learner, "learner", (2, 0))
            or not _unit_matches(units[1], players[1], "opponent", (2, 4))):
        raise ValueError("Unsupported PPO initial units or positions")
    if (game.get_turn_number() != 1
            or game.current_phase != "movement" or game.pending_combats
            or game.combat_log or game.defensive_fire_log
            or game.get_game_status().state != "in_progress"):
        raise ValueError("Unsupported PPO rules, RNG or game state")


def validate_live_game(game, learner):
    """Check fixed rules without restricting core movement or combat."""
    board = game.get_board()
    players = game.get_players()
    if (len(players) != 2 or players[0] is not learner
            or not isinstance(players[1], SeededRandomPlayer)
            or players[1].type is not PlayerType.CPU
            or learner.type is not PlayerType.CPU
            or learner.name != "Learner" or players[1].name != "Opponent"
            or len(learner.factions) != 1
            or len(players[1].factions) != 1
            or learner.factions[0].id != "learner"
            or players[1].factions[0].id != "opponent"):
        raise ValueError("Unsupported PPO player or opponent configuration")
    if (board.rows != 5 or board.columns != 5
            or len(board.hexes) != 25
            or any(board.get_hex(*divmod(i, 5)) is not tile
                   for i, tile in enumerate(board.hexes))
            or board.stacking_limit is not None
            or board.get_road_types() or board.get_road_paths()
            or any(tile.terrain is not None or tile.objectives
                   for tile in board.hexes)):
        raise ValueError("Unsupported PPO board, terrain or objectives")
    resolver = game.defensive_fire_resolver
    if (game.turn_limit is not None or game.reinforcements_deployer.groups
            or resolver.settings != DefensiveFireSettings(0.25)
            or players[1]._board is not board
            or players[1].rng is not resolver.rng):
        raise ValueError("Unsupported PPO rules or RNG")
    if len(board.get_known_units()) != 2:
        raise ValueError("Unsupported PPO known unit count")
    for unit in board.get_known_units():
        if (all(unit.player is not player for player in players)
                or unit.faction is not unit.player.factions[0]
                or unit.id != ("learner" if unit.player is learner
                               else "opponent")
                or unit.type != "Infantry" or unit.echelon is not None
                or (unit.attack, unit.defense, unit.move) != (2, 2, 2)
                or unit.defensive_fire_modifier != 1.0):
            raise ValueError("Unsupported PPO unit attributes")


def _unit_matches(unit, player, name, coords):
    return (unit.player is player and unit.faction is player.factions[0]
            and unit.id == name and unit.name == name.title()
            and unit.type == "Infantry" and unit.echelon is None
            and (unit.attack, unit.defense, unit.move) == (2, 2, 2)
            and unit.get_coords() == coords
            and unit.current_turn_movement_points_remaining == 2
            and unit.defensive_fire_modifier == 1.0
            and unit.ended_last_friendly_turn_with_defensive_fire_eligibility
            and not unit.forced_to_retreat_since_last_friendly_turn
            and not unit.defensive_fire_spent_this_off_turn)
