"""Small, fixed-board, single-unit turn-based learning environment."""

from dataclasses import dataclass
import random

from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.unit.faction import Faction

from .players import LearningPlayer
from .policy_state import action_mask, action_plan, observation
from .scenario import create_game
from .turn_resolution import play_cycle


@dataclass(frozen=True)
class Transition:
    observation: dict
    legal_action_mask: tuple[bool, ...]
    reward: int
    terminated: bool
    truncated: bool
    info: dict


class PPOTrainingEnvironment:
    """One learning move and one opponent turn per step, on a 5x5 board."""

    ROWS = 5
    COLUMNS = 5

    def __init__(self, step_limit=50):
        if isinstance(step_limit, bool) or not isinstance(step_limit, int) \
                or step_limit < 1:
            raise ValueError("step_limit must be a positive integer")
        self.step_limit = step_limit
        self.game = None
        self.step_count = 0
        self.done = False

    def reset(self, seed=None) -> Transition:
        rng = random.Random(seed)
        self.learner = LearningPlayer(
            "Learner", PlayerType.CPU, [Faction("learner", "Learner", "blue")]
        )
        self.game = create_game(self.learner, rng)
        self.rng = rng
        self.step_count = 0
        self.done = False
        return self._transition(None, (), ())

    def step(self, action: int) -> Transition:
        if self.game is None or self.done:
            raise RuntimeError("Reset the environment before stepping")
        mask = self._mask()
        if isinstance(action, bool) or not isinstance(action, int) \
                or not 0 <= action < len(mask) or not mask[action]:
            raise ValueError("Action is not a legal destination")

        destination = self._set_learning_plan(action)
        combat_start = len(self.game.combat_log)
        fire_results = play_cycle(self.game, self.learner, self.rng)
        self.step_count += 1
        self.done = (
            self.game.get_game_status().state == "completed"
            or self.step_count >= self.step_limit
        )
        return self._transition(
            (destination.row, destination.column),
            tuple(fire_results),
            tuple(self.game.combat_log[combat_start:]),
        )

    def _set_learning_plan(self, action):
        plan = action_plan(self.game, self.learner, action)
        self.learner.selected_plan = plan
        return plan.path[-1]

    def _mask(self) -> tuple[bool, ...]:
        return action_mask(self.game, self.learner, active=not self.done)

    def _transition(self, destination, fire_results, combats):
        status = self.game.get_game_status()
        terminated = status.state == "completed"
        truncated = not terminated and self.done
        reward = 0
        if terminated and status.winner_player_name is not None:
            reward = (
                1 if status.winner_player_name == self.learner.name else -1
            )
        return Transition(
            observation=observation(
                self.game, self.learner, self.step_limit - self.step_count
            ),
            legal_action_mask=self._mask(),
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info={
                "outcome": status,
                "turn_number": self.game.get_turn_number(),
                "step_count": self.step_count,
                "destination": destination,
                "defensive_fire": fire_results,
                "combats": combats,
            },
        )
