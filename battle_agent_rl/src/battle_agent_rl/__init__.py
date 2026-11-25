"""Agent policies with independent runtime dependencies."""

__all__ = ["RLPlayer", "QLearningPlayer"]


def __getattr__(name):
    # Keep the package import lightweight for policies that only need core.
    if name == "RLPlayer":
        from .rlplayer import RLPlayer
        return RLPlayer
    if name == "QLearningPlayer":
        from .qlearningplayer import QLearningPlayer
        return QLearningPlayer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
