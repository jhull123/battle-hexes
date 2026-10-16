"""The fixed task's core turn and learner/opponent cycle protocol."""

from battle_hexes_core.combat.combat import Combat


def resolve_combat_phase(game, rng):
    """Finish one side's movement with a single core combat/status pass."""
    Combat(game, rng=rng).resolve_combat()
    game.update_game_status(finalize=True)


def play_turn(game, player, rng, plans=None):
    resolution = game.apply_movement_plans(
        player.movement() if plans is None else plans
    )
    if game.get_game_status().state == "in_progress":
        resolve_combat_phase(game, rng)
    return resolution.defensive_fire_results


def play_cycle(game, learner, rng, learner_plans=None):
    fire_results = list(play_turn(game, learner, rng, learner_plans))
    if game.get_game_status().state == "in_progress":
        game.next_player()
        fire_results.extend(play_turn(game, game.get_current_player(), rng))
        if game.get_game_status().state == "in_progress":
            game.next_player()
    return fire_results
