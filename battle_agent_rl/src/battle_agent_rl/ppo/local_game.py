"""Bounded seeded core-game replay of a frozen PPO checkpoint."""

import argparse
import random

from battle_hexes_core.unit.faction import Faction

from .inference import PPOPlayer
from .gym_env import encode_observation
from .policy_state import action_mask, observation
from .scenario import create_game
from .turn_resolution import play_cycle


def play_local_game(player, seed):
    """Return (decision trace, ending, core status, game) for one seed."""
    rng = random.Random(seed)
    game = create_game(player, rng)
    player.bind_game(game)
    trace = []
    while game.get_game_status().state == "in_progress":
        obs = encode_observation(observation(
            game, player, player.step_limit - player.decisions_issued
        ))
        mask = action_mask(game, player)
        plans = player.movement()
        destination = plans[0].path[-1]
        action = destination.row * 5 + destination.column
        trace.append((obs, mask, action))
        play_cycle(game, player, rng, learner_plans=plans)
        if player.decisions_issued == player.step_limit:
            break
    ending = ("completed" if game.get_game_status().state == "completed"
              else "cutoff")
    return trace, ending, game.get_game_status(), game


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir")
    parser.add_argument(
        "--checkpoint", help="manifest path; defaults to selected"
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    faction = Faction("learner", "Learner", "blue")
    player = PPOPlayer.from_checkpoint(
        "Learner", [faction], args.run_dir, args.checkpoint
    )
    trace, ending, status, game = play_local_game(player, args.seed)
    for number, (obs, mask, action) in enumerate(trace, 1):
        legal = [i for i, allowed in enumerate(mask) if allowed]
        print(f"decision {number}: occupancy={obs['occupancy'].tolist()} "
              f"defensive_fire_ready={obs['defensive_fire_ready'].tolist()} "
              f"remaining_steps={obs['remaining_steps'].tolist()} "
              f"legal={legal} action={action} "
              f"destination={divmod(action, 5)}")
    print(f"ending={ending} core_status={status.state} "
          f"winner={status.winner_player_name} "
          f"defensive_fire={len(game.defensive_fire_log)} "
          f"combat={len(game.combat_log)}")


if __name__ == "__main__":
    main()
