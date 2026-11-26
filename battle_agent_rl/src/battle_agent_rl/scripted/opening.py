"""Configuration and game-local random streams for scripted openings."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from hashlib import sha256
from random import Random
from secrets import randbits
from typing import Literal

from .objective_splits import QuotaVector, sample_objective_quotas

OpeningSampler = Callable[[int, int], QuotaVector]


@dataclass(frozen=True)
class ScriptedOpening:
    """Fresh game options; use ``for_game`` to bind its scripted seats."""

    mode: Literal["deterministic", "randomized"] = "deterministic"
    balanced_probability: int | float = 0.5
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("deterministic", "randomized"):
            raise ValueError("Unknown scripted opening mode")
        p = self.balanced_probability
        if (
            isinstance(p, bool) or not isinstance(p, (int, float))
            or not 0 <= p <= 1
        ):
            raise ValueError("Balanced probability must be between 0 and 1")
        seed = self.seed
        if seed is not None and (
            isinstance(seed, bool) or not isinstance(seed, int)
        ):
            raise ValueError("Scripted opening seed must be an integer")

    def for_game(self) -> "ScriptedGameOpening":
        return ScriptedGameOpening(self)


class ScriptedGameOpening:
    """Share a root seed across seats without sharing their draw sequences."""

    def __init__(self, config: ScriptedOpening) -> None:
        self._config = config
        self._seed = config.seed

    def for_seat(self, seat: int) -> OpeningSampler | None:
        if self._config.mode == "deterministic":
            return None
        return partial(self._sample, seat)

    def _sample(
        self, seat: int, unit_count: int, objective_count: int,
    ) -> QuotaVector:
        rng = None

        def draw(stop: int) -> int:
            nonlocal rng
            if rng is None:
                rng = self._seat_rng(seat)
            return rng.randrange(stop)

        return sample_objective_quotas(
            unit_count, objective_count, self._config.balanced_probability,
            draw,
        )

    def _seat_rng(self, seat: int) -> Random:
        if self._seed is None:
            self._seed = randbits(256)
        key = f"battle-hexes:scripted-opening:v1:{self._seed}:{seat}"
        digest = sha256(key.encode("ascii")).digest()
        return Random(int.from_bytes(digest, "big"))
