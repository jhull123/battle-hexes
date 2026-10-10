"""Small, fixed-board, single-unit turn-based learning environment."""

from dataclasses import dataclass
import random

from battle_hexes_core.combat.combat import Combat
from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)
from battle_hexes_core.game.board import Board
from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.game.unitmovementplan import UnitMovementPlan
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

from .players import LearningPlayer, SeededRandomPlayer


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
        board = Board(self.ROWS, self.COLUMNS)
        learner_faction = Faction("learner", "Learner", "blue")
        opponent_faction = Faction("opponent", "Opponent", "red")
        self.learner = LearningPlayer(
            "Learner", PlayerType.CPU, [learner_faction]
        )
        opponent = SeededRandomPlayer(
            "Opponent", PlayerType.CPU, [opponent_faction], board, rng
        )
        board.add_unit(Unit(
            "learner", "Learner", learner_faction, self.learner,
            "Infantry", 2, 2, 2,
        ), 2, 0)
        board.add_unit(Unit(
            "opponent", "Opponent", opponent_faction, opponent,
            "Infantry", 2, 2, 2,
        ), 2, 4)
        self.game = Game([self.learner, opponent], board, rng=rng)
        self.game.set_defensive_fire_settings(
            DefensiveFireSettings(base_probability=0.25)
        )
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
        fire_results = self._play_cycle()
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
        board = self.game.get_board()
        unit = board.get_units_for_player(self.learner)[0]
        destination = board.get_hex(
            action // self.COLUMNS, action % self.COLUMNS
        )
        start = board.get_hex(*unit.get_coords())
        path = board.shortest_path(unit, start, destination)
        if not path:
            raise RuntimeError("Core could not route a legal destination")
        self.learner.selected_plan = UnitMovementPlan(unit, path)
        return destination

    def _play_cycle(self):
        fire_results = self._play_turn(self.learner)
        if self.game.get_game_status().state == "in_progress":
            self.game.next_player()
            opponent = self.game.get_current_player()
            fire_results.extend(self._play_turn(opponent))
            if self.game.get_game_status().state == "in_progress":
                self.game.next_player()
        return fire_results

    def _play_turn(self, player):
        resolution = self.game.apply_movement_plans(player.movement())
        if self.game.get_game_status().state == "in_progress":
            Combat(self.game, rng=self.rng).resolve_combat()
            self.game.update_game_status(finalize=True)
        return resolution.defensive_fire_results

    def _mask(self) -> tuple[bool, ...]:
        board = self.game.get_board()
        units = board.get_units_for_player(self.learner)
        if self.done or self.game.get_game_status().state != "in_progress" \
                or not units:
            return (False,) * (self.ROWS * self.COLUMNS)
        unit = units[0]
        start = board.get_hex(*unit.get_coords())
        reachable = board.get_reachable_hexes(unit, start)
        return tuple(tile in reachable for tile in board.hexes)

    def _transition(self, destination, fire_results, combats):
        board = self.game.get_board()
        status = self.game.get_game_status()
        terminated = status.state == "completed"
        truncated = not terminated and self.done
        reward = 0
        if terminated and status.winner_player_name is not None:
            reward = (
                1 if status.winner_player_name == self.learner.name else -1
            )
        occupants = tuple(
            board.get_unit_at(tile.row, tile.column) for tile in board.hexes
        )
        occupancy = tuple(self._occupant_value(unit) for unit in occupants)
        defensive_fire_ready = tuple(
            int(unit.public_defensive_fire_status(self.learner))
            if unit is not None else 0
            for unit in occupants
        )

        return Transition(
            observation={
                "occupancy": occupancy,
                "defensive_fire_ready": defensive_fire_ready,
                "remaining_steps": self.step_limit - self.step_count,
            },
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

    def _occupant_value(self, unit):
        if unit is None:
            return 0
        return 1 if self.learner.owns(unit) else -1
