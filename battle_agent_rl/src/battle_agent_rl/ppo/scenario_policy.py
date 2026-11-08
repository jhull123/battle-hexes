"""Explicit task binding and guarded masked inference (no rule execution)."""

from numbers import Integral

import numpy as np

from .scenario_manifest import interface_record, space_record


class ScenarioPolicy:
    """Persisted interface metadata, not spaces alone, authorizes binding."""

    def __init__(self, model, task):
        expected = interface_record(task)
        if getattr(model, "scenario_interface", None) != expected:
            raise ValueError(
                "Incompatible policy contract, seat or slot mapping")
        # Gym Box equality uses allclose; compatibility requires exact bounds.
        if (space_record(model.observation_space) !=
                expected["observation_space"] or
                space_record(model.action_space) != expected["action_space"]):
            raise ValueError("Incompatible checkpoint spaces")
        self.model = model
        self.task = task

    def predict(self, observation, mask, *, deterministic=True):
        mask = np.asarray(mask)
        if (mask.dtype != np.bool_ or
                mask.shape != (self.task.spec.actions,) or not mask.any()):
            raise ValueError("Policy requires a nonempty Boolean action mask")
        if not self.model.observation_space.contains(observation):
            raise ValueError("Incompatible policy observation")
        action, _ = self.model.predict(
            observation, action_masks=mask, deterministic=deterministic)
        if isinstance(action, np.ndarray) and action.shape == ():
            action = action.item()
        if (isinstance(action, bool) or not isinstance(action, Integral) or
                not 0 <= action < len(mask) or not mask[action]):
            raise ValueError("Policy predicted an illegal action")
        return int(action)
