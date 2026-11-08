"""Non-learning controllers over the shared live unit/destination interface."""

import numpy as np

from .decision_actions import action_mask


def choose_action(binding, pending, policy, rng):
    """Sample sorted joint indices, or hold the lowest live slot."""
    legal = np.flatnonzero(action_mask(binding, pending)).tolist()
    if not legal:
        raise RuntimeError("Cannot choose an order from an empty mask")
    if policy == "random":
        return rng.choice(legal)
    if policy != "hold":
        raise ValueError("Controller must be random or hold")
    slot = legal[0] // binding.spec.cells
    row, column = binding.slots[slot].get_coords()
    return (slot * binding.spec.cells
            + row * binding.spec.board_size[1] + column)
