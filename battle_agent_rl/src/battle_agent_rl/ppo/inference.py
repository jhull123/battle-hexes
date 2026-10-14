"""Frozen masked-PPO predictions and the ordinary core Player adapter."""

import numpy as np

from battle_hexes_core.game.player import Player, PlayerType

from .artifacts import load_checkpoint, read_manifest
from .gym_env import encode_observation
from .policy_state import action_mask, action_plan, observation
from .scenario import validate_initial_game, validate_live_game


def predict_action(model, inputs, mask):
    """Predict exactly once, rejecting invalid or unmasked destinations."""
    if not np.any(mask):
        raise ValueError("No legal PPO destination")
    action, _ = model.predict(
        inputs, action_masks=mask, deterministic=True
    )
    if isinstance(action, np.ndarray) and action.shape == ():
        action = action.item()
    if (isinstance(action, (bool, np.bool_))
            or not isinstance(action, (int, np.integer))
            or not 0 <= action < len(mask) or not mask[action]):
        raise ValueError(f"Invalid or illegal PPO prediction: {action}")
    return int(action)


class PPOPlayer(Player):
    """CPU player for the fixed scenario; bind before its first turn."""

    def __init__(self, name, factions, model, step_limit):
        super().__init__(name, PlayerType.CPU, factions)
        if type(step_limit) is not int or step_limit < 1:
            raise ValueError("step_limit must be a positive integer")
        self.model = model
        self._step_limit = step_limit
        self.game = None
        self.decisions_issued = 0
        self._issued_turn = None

    @property
    def step_limit(self):
        """The immutable checkpoint decision budget."""
        return self._step_limit

    @classmethod
    def from_checkpoint(cls, name, factions, run_dir, checkpoint=None,
                        step_limit=None):
        """Load a selected or explicitly named manifest entry, never a zip.

        Before selection, ``checkpoint`` (the manifest path) is required.
        An optional step_limit must equal the manifest's decision budget.
        """
        manifest = read_manifest(run_dir)
        if step_limit is not None and (
                type(step_limit) is not int
                or step_limit != manifest["step_limit"]):
            raise ValueError("Checkpoint step limit mismatch")
        if checkpoint is None:
            entry = manifest["selected"]
            if entry is None:
                raise ValueError(
                    "No selected checkpoint; specify a manifest entry"
                )
        else:
            entry = next((item for item in manifest["checkpoints"]
                          if item["path"] == checkpoint), None)
            if entry is None:
                raise ValueError("Checkpoint not in run manifest")
        model = load_checkpoint(run_dir, entry, manifest,
                                step_limit=manifest["step_limit"])
        return cls(name, factions, model, manifest["step_limit"])

    def bind_game(self, game):
        if game is self.game:
            return self
        if self.game is not None:
            raise ValueError("PPO player is already bound to another game")
        validate_initial_game(game, self)
        self.game = game
        return self

    def movement(self):
        if self.game is None:
            raise RuntimeError("Bind PPO player to a game before movement")
        game = self.game
        if game.get_game_status().state != "in_progress":
            raise RuntimeError("PPO game is completed")
        if game.get_current_player() is not self:
            raise RuntimeError("Not the PPO player's turn")
        if self._issued_turn == game.get_turn_number():
            raise RuntimeError("PPO movement already issued this turn")
        if self.decisions_issued >= self.step_limit:
            raise RuntimeError("PPO decision budget exhausted")
        validate_live_game(game, self)
        board = game.get_board()
        if (len(board.get_units()) != 2
                or len(board.get_units_for_player(self)) != 1
                or len(board.get_units_for_player(game.players[1])) != 1):
            raise RuntimeError("Unsupported PPO live board or unit count")
        inputs = encode_observation(observation(
            game, self, self.step_limit - self.decisions_issued
        ))
        mask = np.array(action_mask(game, self), dtype=np.bool_)
        action = predict_action(self.model, inputs, mask)
        plan = action_plan(game, self, action)
        self.decisions_issued += 1
        self._issued_turn = game.get_turn_number()
        return [plan]

    def combat_results(self, combat_results):
        pass
