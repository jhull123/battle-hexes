"""One frozen masked PPO decision applied through the live core turn path."""

from dataclasses import dataclass

from battle_agent_rl.ppo.multi_unit_state import joint_mask, slot_observation
from battle_agent_rl.ppo.playable_scenario import TURN_LIMIT, slots_for_game
from battle_agent_rl.ppo.playable_turn import apply_order
from battle_hexes_api.ppo_artifact import configured_model
from battle_hexes_api.ppo_state import (capture_rng, is_ppo_game,
                                        validate_state)
from battle_hexes_api.persistence.command_errors import CommandErrorTranslator


@dataclass(frozen=True)
class OrderResult:
    plan: object
    fire: tuple
    combats: tuple


class PpoOrderAdapter:
    def __call__(self, game):
        from battle_agent_rl.ppo.multi_unit_gym import predict_joint_action

        if not is_ppo_game(game):
            raise CommandErrorTranslator.error(409, "invalidPpoTurn")
        validate_state(game.ppo_state, game)
        if game.current_player is not game.players[0] or \
                game.current_phase != "movement":
            raise CommandErrorTranslator.error(409, "invalidPpoTurn")
        try:
            model, _ = configured_model(game.ppo_state["checkpoint_digest"])
        except ValueError as error:
            raise CommandErrorTranslator.error(
                503, "ppoArtifactUnavailable") from error
        slots = slots_for_game(game)
        pending = [unit_id in game.ppo_state["pending_unit_ids"]
                   for unit_id in (slots[0].id, slots[1].id)]
        mask = joint_mask(game, slots[:2], pending)
        if not any(mask):
            raise CommandErrorTranslator.error(409, "invalidPpoTurn")
        observation = slot_observation(
            game, slots, pending, TURN_LIMIT + 1 - game.turn_number,
            game.players[0])
        try:
            action = predict_joint_action(model, observation, mask)
            plan, fire, combats = apply_order(game, slots[:2], pending,
                                              action, game.ppo_rng)
        except (ValueError, RuntimeError) as error:
            raise CommandErrorTranslator.error(
                409, "ppoPredictionInvalid") from error
        game.ppo_state["pending_unit_ids"] = [
            slots[index].id for index in range(2) if pending[index]
        ] if game.current_player is game.players[0] else []
        capture_rng(game)
        return OrderResult(plan, fire, combats)
