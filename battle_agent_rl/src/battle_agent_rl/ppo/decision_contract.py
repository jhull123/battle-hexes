"""Task-supplied decision dimensions, bounds and exact policy spaces."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ObservationBounds:
    unit_stats_high: float
    movement_high: int
    terrain_low: float
    terrain_high: float
    road_high: float
    objective_points_high: int
    score_high: int
    reinforcement_high: int


@dataclass(frozen=True)
class DecisionSpec:
    board_size: tuple[int, int]
    learner_seat: int
    learner_ids: tuple[str, ...]
    opponent_ids: tuple[str, ...]
    objective_coords: tuple[tuple[int, int], ...]
    reinforcement_ids: tuple[str, ...]
    turn_limit: int
    bounds: ObservationBounds

    def __post_init__(self):
        if (self.learner_seat not in (0, 1) or min(self.board_size) < 1
                or not self.learner_ids or not self.opponent_ids
                or self.turn_limit < 1
                or len(set(self.slot_ids)) != len(self.slot_ids)
                or len(set(self.reinforcement_ids)) !=
                len(self.reinforcement_ids)):
            raise ValueError("Invalid decision dimensions, seat or identities")

    @property
    def slot_ids(self):
        return self.learner_ids + self.opponent_ids

    @property
    def cells(self):
        return self.board_size[0] * self.board_size[1]

    @property
    def actions(self):
        return len(self.learner_ids) * self.cells


@dataclass(frozen=True)
class ScenarioTask:
    """An explicitly supported task, not a multi-scenario training registry."""

    scenario_id: str
    scenario_version: str
    gameplay_sha256: str
    contract: str
    learner_seat: int
    learner_ids: tuple[str, ...]
    opponent_ids: tuple[str, ...]
    bounds: ObservationBounds

    def decision_spec(self, scenario):
        return DecisionSpec(
            scenario.board_size, self.learner_seat, self.learner_ids,
            self.opponent_ids,
            tuple(o.coords for o in scenario.objectives or ()),
            tuple(g.id for g in scenario.reinforcements or ()),
            scenario.turn_limit, self.bounds)


def observation_space(spec):
    """Keep Gymnasium optional for read-only core-state inspection."""
    from gymnasium import spaces

    units, cells = len(spec.slot_ids), spec.cells
    bounds = spec.bounds
    objectives = len(spec.objective_coords)
    return spaces.Dict({
        "positions": spaces.MultiBinary((units, cells)),
        "unit_status": spaces.Box(0, 2, (units,), dtype=np.int8),
        "unit_stats": spaces.Box(
            0, bounds.unit_stats_high, (units, 4), dtype=np.float32),
        "movement_remaining": spaces.Box(
            0, bounds.movement_high, (units,), dtype=np.int8),
        "fire_flags": spaces.MultiBinary((units, 4)),
        "pending": spaces.MultiBinary(len(spec.learner_ids)),
        "terrain": spaces.Box(
            bounds.terrain_low, bounds.terrain_high, (cells, 3),
            dtype=np.float32),
        "road_edges": spaces.Box(
            0, bounds.road_high, (cells, 6), dtype=np.float32),
        "objective_points": spaces.Box(
            0, bounds.objective_points_high, (cells,), dtype=np.int8),
        "objective_control": (spaces.MultiBinary(objectives) if objectives else
                              spaces.Box(0, 1, (0,), dtype=np.int8)),
        "scores": spaces.Box(0, bounds.score_high, (2,), dtype=np.int8),
        "reinforcement": spaces.Box(
            0, bounds.reinforcement_high,
            (len(spec.reinforcement_ids), 4), dtype=np.int32),
        "remaining_cycles": spaces.Box(
            0, spec.turn_limit, (1,), dtype=np.int32),
    })


def action_space(spec):
    from gymnasium import spaces

    return spaces.Discrete(spec.actions)
