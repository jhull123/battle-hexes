"""Uniform rank selection over ordered objective quota vectors."""

from collections.abc import Callable
from dataclasses import dataclass
from math import comb

QuotaVector = tuple[int, ...]
BoundedDraw = Callable[[int], int]


def sample_objective_quotas(
    unit_count: int,
    objective_count: int,
    balanced_probability: int | float,
    draw: BoundedDraw,
) -> QuotaVector:
    """Draw a family, then unrank a uniform member without materializing it."""
    if objective_count == 0:
        return ()

    space = _QuotaSpace(unit_count, objective_count)
    total, balanced_count = space.suffix_counts(unit_count, objective_count)
    unbalanced_count = total - balanced_count
    balanced = _choose_balanced(balanced_probability, unbalanced_count, draw)
    family_count = balanced_count if balanced else unbalanced_count
    rank = draw(family_count) if family_count > 1 else 0
    return space.unrank(balanced, rank)


def _choose_balanced(
    probability: int | float, unbalanced_count: int, draw: BoundedDraw,
) -> bool:
    if unbalanced_count == 0 or probability == 1:
        return True
    if probability == 0:
        return False
    numerator, denominator = probability.as_integer_ratio()
    return draw(denominator) < numerator


@dataclass(frozen=True)
class _QuotaSpace:
    units: int
    objectives: int

    @property
    def base_quota(self) -> int:
        return self.units // self.objectives

    def suffix_counts(self, units: int, objectives: int) -> tuple[int, int]:
        """Count all suffixes and those compatible with a balanced prefix."""
        total = comb(units + objectives - 1, objectives - 1)
        extras = units - self.base_quota * objectives
        balanced = comb(objectives, extras) if 0 <= extras <= objectives else 0
        return total, balanced

    def unrank(self, balanced: bool, rank: int) -> QuotaVector:
        remaining = self.units
        prefix_is_balanced = True
        quotas = []
        for objectives_left in range(self.objectives - 1, 0, -1):
            quota, rank, prefix_is_balanced = self._next_quota(
                remaining, objectives_left, balanced, rank, prefix_is_balanced,
            )
            quotas.append(quota)
            remaining -= quota
        return (*quotas, remaining)

    def _next_quota(
        self, remaining: int, objectives_left: int, balanced: bool,
        rank: int, prefix_is_balanced: bool,
    ) -> tuple[int, int, bool]:
        base = self.base_quota
        candidates = (
            range(base, min(remaining, base + 1) + 1)
            if balanced else range(remaining + 1)
        )
        for quota in candidates:
            valid_prefix = prefix_is_balanced and base <= quota <= base + 1
            total, even = self.suffix_counts(
                remaining - quota, objectives_left,
            )
            if not valid_prefix:
                even = 0
            count = even if balanced else total - even
            if rank < count:
                return quota, rank, valid_prefix
            rank -= count
        raise AssertionError("Quota rank out of range")
