"""Live one-order-per-unit turn driver for the 9x9 prototype."""

from dataclasses import dataclass
import random

from .multi_unit_scenario import create_multi_unit_game
from .multi_unit_state import joint_mask, joint_plan, slot_observation
from .turn_resolution import resolve_combat_phase


@dataclass(frozen=True)
class Transition:
    observation: dict
    legal_action_mask: tuple[bool, ...]
    reward: int
    terminated: bool
    truncated: bool
    info: dict


class MultiUnitEnvironment:
    """One learner order per step; resolve both sides once per cycle."""

    def __init__(self, cycle_limit=50, learner_count=2, opponent_count=2):
        if isinstance(cycle_limit, bool) or not isinstance(cycle_limit, int) \
                or cycle_limit < 1:
            raise ValueError("cycle_limit must be a positive integer")
        self.cycle_limit = cycle_limit
        self.learner_count = learner_count
        self.opponent_count = opponent_count
        self.game = None
        self.done = False

    def reset(self, seed=None):
        self.rng = random.Random(seed)
        self.game, self.learner, self.opponent, self.slots = (
            create_multi_unit_game(self.rng, self.learner_count,
                                   self.opponent_count))
        self.pending = self._living((0, 1))
        self.completed_cycles = 0
        self.decision_count = 0
        self.done = False
        return self._transition(None, (), ())

    def _living(self, indexes):
        board_units = self.game.get_board().get_units()
        return [self.slots[i] is not None and self.slots[i] in board_units
                for i in indexes]

    def _active(self):
        return self.game.get_game_status().state == "in_progress"

    def _move(self, slots, pending, action):
        slot, plan = joint_plan(self.game, slots, pending, action)
        result = self.game.apply_movement_plans([plan])
        pending[slot] = False
        return slot, plan.path[-1], result.defensive_fire_results

    def step(self, action):
        if self.game is None or self.done:
            raise RuntimeError("Reset the environment before stepping")
        # Validate before reading event offsets or advancing RNG.
        joint_plan(self.game, self.slots[:2], self.pending, action)
        combat_start = len(self.game.combat_log)
        fire_start = len(self.game.defensive_fire_log)
        slot, destination, _ = self._move(
            self.slots[:2], self.pending, action)
        self.decision_count += 1
        self._prune_pending(self.pending, (0, 1))
        if self._active() and not any(self.pending):
            self._finish_cycle()
        self.done = not self._active() or (
            self.completed_cycles >= self.cycle_limit)
        if self.done:
            self.pending = [False, False]
        return self._transition(
            (slot, destination.row, destination.column),
            tuple(self.game.defensive_fire_log[fire_start:]),
            tuple(self.game.combat_log[combat_start:]))

    def _prune_pending(self, pending, indexes):
        living = self._living(indexes)
        for index, alive in enumerate(living):
            pending[index] = pending[index] and alive

    def _finish_cycle(self):
        resolve_combat_phase(self.game, self.rng)
        if not self._active():
            return
        self.game.next_player()
        if not self._active():
            return
        pending = self._living((2, 3))
        while self._active() and any(pending):
            mask = joint_mask(self.game, self.slots[2:], pending)
            if not any(mask):
                raise RuntimeError("Active opponent has no legal action")
            action = self.rng.choice([i for i, legal in enumerate(mask)
                                      if legal])
            self._move(self.slots[2:], pending, action)
            self._prune_pending(pending, (2, 3))
        if self._active():
            resolve_combat_phase(self.game, self.rng)
            self.completed_cycles += 1
            if self._active():
                self.game.next_player()
                if self._active():
                    self.pending = self._living((0, 1))

    def _transition(self, destination, fire, combats):
        status = self.game.get_game_status()
        terminated = status.state == "completed"
        truncated = not terminated and self.done
        reward = 0
        if terminated and status.winner_player_name is not None:
            reward = (1 if status.winner_player_name == self.learner.name
                      else -1)
        mask = joint_mask(self.game, self.slots[:2], self.pending,
                          active=not self.done)
        if not self.done and not any(mask):
            raise RuntimeError("Active learner has no legal action")
        return Transition(
            slot_observation(self.game, self.slots, self.pending,
                             self.cycle_limit - self.completed_cycles,
                             self.learner),
            mask, reward, terminated, truncated,
            {"outcome": status, "turn_number": self.game.get_turn_number(),
             "decision_count": self.decision_count,
             "completed_cycles": self.completed_cycles,
             "destination": destination, "defensive_fire": fire,
             "combats": combats})
