from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import product
from random import Random
from unittest.mock import Mock

import pytest

from battle_agent_rl.scripted import ScriptedGameOpening, ScriptedOpening
from battle_agent_rl.scripted.balanced_assignment import exact_target_indices
from battle_agent_rl.scripted.objective_splits import sample_objective_quotas


def _vectors(units, objectives):
    return [split for split in product(range(units + 1), repeat=objectives)
            if sum(split) == units]


def _balanced(split):
    return max(split) - min(split) <= 1


def _draw_split(units, objectives, probability, draws):
    draws = iter(draws)

    def draw(stop):
        expected_stop, value = next(draws)
        assert stop == expected_stop
        return value

    split = sample_objective_quotas(units, objectives, probability, draw)
    assert next(draws, None) is None
    return split


def _distribution(units, objectives, probability):
    vectors = _vectors(units, objectives)
    p = Fraction(probability)
    masses = Counter()
    for ticket in range(p.denominator):
        family = [v for v in vectors if _balanced(v) == (ticket < p.numerator)]
        family_draw = [(p.denominator, ticket)] if 0 < p < 1 else []
        for rank, expected in enumerate(family):
            rank_draw = [(len(family), rank)] if len(family) > 1 else []
            split = _draw_split(
                units, objectives, probability, family_draw + rank_draw,
            )
            assert split == expected
            masses[split] += Fraction(1, p.denominator * len(family))
    assert sum(masses.values()) == 1
    return masses


def test_crossroads_distribution_exactly_without_frequency_estimates():
    masses = _distribution(6, 3, ScriptedOpening().balanced_probability)
    assert masses.pop((2, 2, 2)) == Fraction(1, 2)
    assert len(masses) == 27
    assert all(mass == Fraction(1, 54) for mass in masses.values())
    assert {(6, 0, 0), (0, 6, 0), (0, 0, 6)} <= masses.keys()


@pytest.mark.parametrize("p", [0, 0.5, 0.75, 1])
def test_uneven_splits_are_uniform_within_each_family(p):
    masses = _distribution(5, 3, p)
    balanced = {(1, 2, 2), (2, 1, 2), (2, 2, 1)}
    assert {v for v in masses if _balanced(v)} == (balanced if p else set())
    assert len(masses.keys() - balanced) == (18 if p < 1 else 0)
    assert all(masses[v] == Fraction(p) / 3 for v in balanced)
    assert all(masses[v] == (1 - Fraction(p)) / 18
               for v in masses.keys() - balanced)


@pytest.mark.parametrize(("units", "objectives", "expected"), [
    (6, 1, (6,)),
    (0, 3, (0, 0, 0)),
    (6, 0, ()),
    (0, 0, ()),
])
def test_no_draw_for_a_single_split_or_no_objectives(units, objectives,
                                                     expected):
    assert _draw_split(units, objectives, 0, []) == expected


def test_single_family_skips_family_draw_but_still_selects_rank():
    assert [
        _draw_split(1, 3, 0, [(3, rank)]) for rank in range(3)
    ] == [(0, 0, 1), (0, 1, 0), (1, 0, 0)]
    assert _draw_split(2, 2, 0, [(2, 1)]) == (2, 0)


@pytest.mark.parametrize(("units", "objectives"), [(2, 4), (3, 2), (4, 4)])
def test_rank_enumeration_includes_unbalanced_prefixes_and_zero_quotas(
    units, objectives,
):
    assert set(_distribution(units, objectives, 0.5)) == set(
        _vectors(units, objectives),
    )


@pytest.mark.parametrize("options", [
    {"mode": "other"}, {"balanced_probability": True},
    {"balanced_probability": "0.5"}, {"balanced_probability": -0.1},
    {"balanced_probability": 1.1}, {"balanced_probability": float("nan")},
    {"balanced_probability": float("inf")},
])
def test_invalid_opening_options_are_rejected(options):
    with pytest.raises(ValueError):
        ScriptedOpening(**options)


def test_seedless_game_reads_system_entropy_only_when_needed(monkeypatch):
    entropy = Mock(side_effect=[0, 123])
    monkeypatch.setattr("battle_agent_rl.scripted.opening.randbits",
                        entropy)
    config = ScriptedOpening(mode="randomized")
    first = ScriptedGameOpening()
    assert first.for_seat(0, config)(0, 3) == (0, 0, 0)
    assert first.for_seat(1, config)(6, 1) == (6,)
    entropy.assert_not_called()
    seeded = ScriptedGameOpening(seed=0)
    expected = [seeded.for_seat(seat, config)(6, 3) for seat in range(2)]
    actual = [first.for_seat(seat, config)(6, 3) for seat in range(2)]
    assert actual == expected
    assert entropy.call_count == 1
    second = ScriptedGameOpening()
    seeded = ScriptedGameOpening(seed=123)
    assert second.for_seat(0, config)(6, 3) == seeded.for_seat(0, config)(6, 3)
    assert entropy.call_count == 2


def test_explicit_seed_uses_the_specified_seat_stream(monkeypatch):
    monkeypatch.setattr("battle_agent_rl.scripted.opening.randbits",
                        lambda _: pytest.fail("requested entropy"))
    config = ScriptedOpening(mode="randomized")
    opening = ScriptedGameOpening(seed=0)
    for seat in range(2):
        digest = sha256(f"battle-hexes:scripted-opening:v1:0:{seat}".encode())
        rng = Random(int.from_bytes(digest.digest(), "big"))
        expected = sample_objective_quotas(6, 3, 0.5, rng.randrange)
        assert opening.for_seat(seat, config)(6, 3) == expected


@pytest.mark.parametrize("distances", [
    [[4, 6], [1, 9], [9, 1]],
    [[4, 0], [5, 1], [6, 2]],
    [[1, 0, 4], [1, 1, 1], [0, 3, 1], [0, 1, 0]],
])
def test_exact_solver_matches_exhaustive_reference_for_all_small_quotas(
    distances,
):
    objectives = len(distances[0])
    for quotas in _vectors(len(distances), objectives):
        _, expected = min(
            (sum(row[target] for row, target in zip(distances, targets)),
             targets)
            for targets in product(range(objectives), repeat=len(distances))
            if tuple(targets.count(i) for i in range(objectives)) == quotas
        )
        assert exact_target_indices(distances, quotas) == list(expected)
