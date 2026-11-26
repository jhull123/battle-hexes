from itertools import product
from random import Random

import pytest

from battle_agent_rl.scripted.balanced_assignment import (
    balanced_target_indices,
)


def _exhaustive_optimum(matrix, target_count):
    def rank(targets):
        distance = sum(row[target] for row, target in zip(matrix, targets))
        return distance, targets

    balanced = []
    for targets in product(range(target_count), repeat=len(matrix)):
        counts = [targets.count(t) for t in range(target_count)]
        if max(counts) - min(counts) <= 1:
            balanced.append(targets)
    return list(min(balanced, key=rank))


@pytest.mark.parametrize(
    "units,targets", list(product(range(1, 6), range(1, 5))),
)
def test_exact_solution_matches_exhaustive_search(units, targets):
    rng = Random(0)
    for _ in range(20):
        matrix = [[rng.randrange(5) for _ in range(targets)]
                  for _ in range(units)]
        assert balanced_target_indices(matrix) == _exhaustive_optimum(
            matrix, targets
        )
