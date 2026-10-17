"""Ownership and phase checks for the non-PPO side of a PPO game."""

from battle_hexes_api.ppo_state import is_ppo_game
from battle_hexes_api.persistence.command_errors import CommandErrorTranslator


def reject_ppo_command():
    raise CommandErrorTranslator.error(409, "invalidPpoTurn")


def require_opponent(game, phase):
    if not is_ppo_game(game):
        return
    if (game.current_player is not game.players[1]
            or game.current_phase != phase):
        reject_ppo_command()


def require_human(game, phase):
    require_opponent(game, phase)
    if is_ppo_game(game) and game.player_type_ids[1] != "human":
        reject_ppo_command()


def require_cpu_opponent(game):
    require_opponent(game, "movement")
    if is_ppo_game(game) and game.player_type_ids[1] not in (
            "random", "q-learning"):
        reject_ppo_command()


def check_opponent_board(game, sparse_board):
    """No client can reposition a PPO unit or alter a resolved prior phase."""
    units = {unit.id: unit for unit in game.board.get_units()}
    if len(sparse_board.units) != len(units) or \
            {str(unit.id) for unit in sparse_board.units} != set(units):
        reject_ppo_command()
    for saved in sparse_board.units:
        unit = units[str(saved.id)]
        destination = (saved.row, saved.column)
        if unit.get_coords() == destination:
            continue
        if unit.player is game.players[0] or game.current_phase != "movement":
            reject_ppo_command()
        board = game.board
        start = board.get_hex(*unit.get_coords())
        target = board.get_hex(*destination)
        if (target is None or target not in board.get_reachable_hexes(
                unit, start, unit.current_turn_movement_points_remaining)):
            reject_ppo_command()
