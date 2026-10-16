"""Core-loaded 50-turn 2v2 environment; external cap never changes input."""

import random

from .multi_unit_environment import Transition
from .multi_unit_state import joint_mask, slot_observation
from .playable_scenario import create_game
from .playable_turn import apply_order


class PlayableEnvironment:
    def __init__(self, cycle_limit=50):
        if type(cycle_limit) is not int or not 1 <= cycle_limit <= 50:
            raise ValueError("cycle_limit must be between 1 and 50")
        self.cycle_limit = cycle_limit
        self.game = None

    def reset(self, seed=None):
        self.rng = random.Random(seed)
        self.game, self.learner, _, self.slots = create_game(self.rng)
        self.pending = [True, True]
        self.decisions = 0
        self.done = False
        return self._transition((), ())

    def step(self, action):
        if self.game is None or self.done:
            raise RuntimeError("Reset before stepping")
        _, fire, combats = apply_order(
            self.game, self.slots[:2], self.pending, action, self.rng)
        self.decisions += 1
        if self.game.current_player is self.game.players[1]:
            self._opponent_turn()
        self.done = (self.game.get_game_status().state == "completed"
                     or self.game.turn_number > self.cycle_limit)
        if self.done:
            self.pending = [False, False]
        return self._transition(fire, combats)

    def _opponent_turn(self):
        pending = [unit.get_coords() is not None for unit in self.slots[2:]]
        while (self.game.get_game_status().state == "in_progress"
               and any(pending)):
            mask = joint_mask(self.game, self.slots[2:], pending)
            action = self.rng.choice([i for i, legal in enumerate(mask)
                                      if legal])
            apply_order(self.game, self.slots[2:], pending, action, self.rng)
        if self.game.current_player is self.learner:
            self.pending = [unit.get_coords() is not None
                            for unit in self.slots[:2]]

    def _transition(self, fire, combats):
        status = self.game.get_game_status()
        completed = status.state == "completed"
        if completed:
            outcome = ("win" if status.winner_player_name == self.learner.name
                       else "draw" if status.winner_player_name is None
                       else "loss")
        else:
            outcome = "cutoff" if self.done else None
        return Transition(
            slot_observation(self.game, self.slots, self.pending,
                             max(0, 51 - self.game.turn_number), self.learner),
            joint_mask(self.game, self.slots[:2], self.pending,
                       active=not self.done),
            1 if outcome == "win" else -1 if outcome == "loss" else 0,
            completed, self.done and not completed,
            {"outcome": outcome, "core_status": status.state,
             "decision_count": self.decisions, "defensive_fire": fire,
             "combats": combats})
