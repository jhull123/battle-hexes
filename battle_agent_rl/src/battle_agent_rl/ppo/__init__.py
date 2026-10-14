"""PPO training environment and its game-player adapters."""

from .environment import PPOTrainingEnvironment, Transition

__all__ = ["PPOTrainingEnvironment", "Transition", "PPOPlayer"]


def __getattr__(name):
    # Keep the random baseline importable without Gymnasium/SB3.
    if name == "PPOPlayer":
        from .inference import PPOPlayer
        return PPOPlayer
    raise AttributeError(name)
