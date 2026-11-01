"""Fixed Wehrmacht state/action contract; no environment or trainer adapter."""

import numpy as np


CONTRACT = (
    "battle-hexes-crossroads-wehrmacht-unit-destination-live-turnlimit8-v1")
SCENARIO_ID = "d_day_crossroads"
SCENARIO_VERSION = "1"
TURN_LIMIT = 8
COLUMNS = 18
CELLS = 324
ACTIONS = 1620
LEARNER_IDS = ("A / Inf. Zug", "B / Inf. Zug", "Crossroads Feldwache",
               "MG Trupp A", "StuG. III Zug A")
SLOT_IDS = LEARNER_IDS + tuple(f"Airborne Inf. {c}" for c in "ABCDEF")


def observation_space():
    """Declare exact spaces lazily for lightweight core-state inspection."""
    from gymnasium import spaces

    return spaces.Dict({
        "positions": spaces.MultiBinary((11, CELLS)),
        "unit_status": spaces.Box(0, 2, (11,), dtype=np.int8),
        "unit_stats": spaces.Box(0, 7, (11, 4), dtype=np.float32),
        "movement_remaining": spaces.Box(0, 7, (11,), dtype=np.int8),
        "fire_flags": spaces.MultiBinary((11, 4)),
        "pending": spaces.MultiBinary(5),
        "terrain": spaces.Box(-2, 3, (CELLS, 3), dtype=np.float32),
        "road_edges": spaces.Box(0, 1, (CELLS, 6), dtype=np.float32),
        "objective_points": spaces.Box(0, 1, (CELLS,), dtype=np.int8),
        "objective_control": spaces.MultiBinary(3),
        "scores": spaces.Box(0, 3, (2,), dtype=np.int8),
        "reinforcement": spaces.Box(0, 17, (1, 4), dtype=np.int32),
        "remaining_cycles": spaces.Box(0, 8, (1,), dtype=np.int32),
    })


def action_space():
    from gymnasium import spaces

    return spaces.Discrete(ACTIONS)
