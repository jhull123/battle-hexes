"""Non-learning scenario environment: live orders, core turns and endings."""

from dataclasses import replace
import random

from battle_hexes_core.scoring.objective_scorer import ObjectiveScorer

from .decision_actions import (
    action_mask, action_plan, pending_at_movement_start,
)
from .decision_binding import bind_decision
from .decision_controller import choose_action
from .decision_observation import observation
from .live_turn import apply_live_plan, finish_side
from .multi_unit_environment import Transition


class ScenarioEnvironment:
    """Scenario facts come from a task; its explicit seat selects the learner.

    Every active return is a learner movement decision. Internal empty turns
    use the same phase workflow as ordered turns, without a synthetic action.
    One seeded RNG is shared by core and opponent, never by the learner.
    An optional opponent controller(binding, pending_ids) supplies one explicit
    order at a time; waiting for human input preserves execution semantics.
    """

    def __init__(self, task, cycle_limit=None, opponent_policy="random"):
        horizon = task.spec.turn_limit
        if cycle_limit is None:
            cycle_limit = horizon
        if type(cycle_limit) is not int or not 1 <= cycle_limit <= horizon:
            raise ValueError(f"cycle_limit must be between 1 and {horizon}")
        if not callable(opponent_policy) and opponent_policy not in (
                "random", "hold"):
            raise ValueError(
                "opponent_policy must be random, hold or a controller")
        self.task = task
        self.cycle_limit = cycle_limit
        self.opponent_policy = opponent_policy
        self.game = None
        self.done = False

    def reset(self, seed=None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.binding = self.task.create_game(self.rng)
        self.game = self.binding.game
        self.learner = self.binding.learner
        spec = self.task.spec
        self.opponent_binding = bind_decision(self.game, replace(
            spec, learner_seat=1 - spec.learner_seat,
            learner_ids=spec.opponent_ids, opponent_ids=spec.learner_ids))
        self.pending = set()
        self._turn_key = None
        self.decision_count = 0
        self.done = False
        ObjectiveScorer().recalculate_scenario_victory(self.game)
        orders = []
        self._advance(orders)
        # Opening fire/combat and any initial deployment belong to reset.
        return self._transition((0, 0, 0), orders)

    def step(self, action):
        if self.game is None or self.done:
            raise RuntimeError("Reset before stepping")
        # Validation is read-only, including core path/budget validation. No
        # counters, pending IDs, event offsets or RNG advance on invalid input.
        _, plan = action_plan(self.binding, self.pending, action)
        offsets = self._event_offsets()
        orders = [self._order_record(self.binding, action, plan)]
        apply_live_plan(self.game, plan, self.pending, self.rng,
                        score_objectives=True)
        self.decision_count += 1
        self._advance(orders)
        return self._transition(offsets, orders)

    def action_masks(self):
        if self.game is None:
            raise RuntimeError("Reset before requesting masks")
        return action_mask(self.binding, self.pending, active=not self.done)

    def _advance(self, orders):
        while True:
            if self.game.finalize_completed_phase():
                self.done = True
            elif self.game.turn_number > self.cycle_limit:
                # Core's wrap (including arrival) is retained, but the next
                # first-seat turn must not act. Core completion wins this race.
                self.done = True
            if self.done:
                self.pending.clear()
                return
            binding = (self.binding if self.game.current_player is self.learner
                       else self.opponent_binding)
            key = (self.game.turn_number, self.game.current_player)
            if key != self._turn_key:
                self.pending = set(pending_at_movement_start(binding))
                self._turn_key = key
            if not self.pending:
                finish_side(self.game, self.rng, score_objectives=True)
            elif binding is self.binding:
                return
            else:
                self._opponent_order(binding, orders)

    def _opponent_order(self, binding, orders):
        # An explicit-order controller may block awaiting human input. It uses
        # exactly the substitute controller's conversion/execution path.
        action = (self.opponent_policy(binding, frozenset(self.pending))
                  if callable(self.opponent_policy) else
                  choose_action(binding, self.pending,
                                self.opponent_policy, self.rng))
        _, plan = action_plan(binding, self.pending, action)
        orders.append(self._order_record(binding, action, plan))
        apply_live_plan(self.game, plan, self.pending, self.rng,
                        score_objectives=True)

    def _order_record(self, binding, action, plan):
        return {"role": "learner" if binding is self.binding else "opponent",
                "turn_number": self.game.turn_number,
                "action": int(action), "unit_id": plan.unit.id,
                "path": tuple((h.row, h.column) for h in plan.path)}

    def _event_offsets(self):
        return (len(self.game.defensive_fire_log), len(self.game.combat_log),
                len(self.game.reinforcements_deployer.game_log))

    def _transition(self, offsets, orders):
        status = self.game.get_game_status()
        completed = status.state == "completed"
        outcome = "cutoff" if self.done else None
        if completed:
            outcome = ("draw" if status.winner_player_name is None else
                       "win" if status.winner_player_name == self.learner.name
                       else "loss")
        inputs = observation(self.binding, self.pending, active=not self.done)
        mask = self.action_masks()
        if not self.done and not mask.any():
            raise RuntimeError("Active learner has no legal action")
        fire, combat, arrival = offsets
        return Transition(
            inputs, mask, {"win": 1, "loss": -1}.get(outcome, 0),
            completed, self.done and not completed,
            {"outcome": outcome, "core_status": status.state,
             "core_reason": status.reason, "winner": status.winner_player_name,
             "scores": inputs["scores"].tolist(),
             "turn_number": self.game.turn_number,
             "decision_count": self.decision_count,
             "orders": tuple(orders),
             "defensive_fire": tuple(self.game.defensive_fire_log[fire:]),
             "combats": tuple(self.game.combat_log[combat:]),
             "reinforcements": tuple(
                 self.game.reinforcements_deployer.game_log[arrival:])})
