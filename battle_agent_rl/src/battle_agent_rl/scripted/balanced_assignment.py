"""Minimum-distance assignment for a matrix in stable unit/objective order."""

import heapq
from dataclasses import dataclass


@dataclass(slots=True)
class _Arc:
    to: int
    reverse: int
    capacity: int
    cost: int


class _AssignmentFlow:
    """Send one unit at a time along minimum-cost residual paths."""

    def __init__(self, size: int):
        self._graph: list[list[_Arc]] = [[] for _ in range(size)]
        self._potential = [0] * size

    def connect(
        self, start: int, end: int, capacity: int, cost: int = 0,
    ) -> None:
        forward = _Arc(end, len(self._graph[end]), capacity, cost)
        reverse = _Arc(start, len(self._graph[start]), 0, -cost)
        self._graph[start].append(forward)
        self._graph[end].append(reverse)

    def send_one(self, source: int, sink: int) -> None:
        distances, previous = self._shortest_paths(source)
        for node, distance in enumerate(distances):
            if distance is not None:
                self._potential[node] += distance
        node = sink
        while node != source:
            step = previous[node]
            assert step is not None  # quotas always admit a full assignment
            start, arc = step
            arc.capacity -= 1
            self._graph[node][arc.reverse].capacity += 1
            node = start

    def _shortest_paths(
        self, source: int,
    ) -> tuple[list[int | None], list[tuple[int, _Arc] | None]]:
        distances: list[int | None] = [None] * len(self._graph)
        previous: list[tuple[int, _Arc] | None] = [None] * len(self._graph)
        distances[source] = 0
        queue = [(0, source)]
        while queue:
            distance, node = heapq.heappop(queue)
            if distances[node] != distance:
                continue
            for arc in self._graph[node]:
                if not arc.capacity:
                    continue
                # Node potentials keep reduced costs nonnegative even on
                # reverse arcs that can undo an earlier assignment.
                cost = (
                    arc.cost + self._potential[node] - self._potential[arc.to]
                )
                candidate = distance + cost
                best = distances[arc.to]
                if best is None or candidate < best:
                    distances[arc.to] = candidate
                    previous[arc.to] = (node, arc)
                    heapq.heappush(queue, (candidate, arc.to))
        return distances, previous

    def target_used_by(self, unit: int, first_target: int) -> int:
        return next(
            arc.to - first_target
            for arc in self._graph[unit]
            if arc.to >= first_target and arc.capacity == 0
        )


def balanced_target_indices(distances: list[list[int]]) -> list[int]:
    """Return the first minimum-distance balanced solution in lexical order."""
    return _target_indices(distances, None)


def exact_target_indices(
    distances: list[list[int]], quotas: tuple[int, ...],
) -> list[int]:
    """Return the first minimum-distance solution that fills exact quotas."""
    if (
        any(type(quota) is not int or quota < 0 for quota in quotas)
        or sum(quotas) != len(distances)
        or (distances and len(quotas) != len(distances[0]))
    ):
        raise ValueError("Quotas must match the unit and objective counts")
    return _target_indices(distances, quotas)


def _target_indices(
    distances: list[list[int]], quotas: tuple[int, ...] | None,
) -> list[int]:
    unit_count = len(distances)
    if not unit_count:
        return []
    target_count = len(distances[0])
    if not target_count:
        return []
    if target_count == 1:
        return [0] * unit_count

    source = unit_count
    first_target = source + 1
    extras = first_target + target_count
    sink = extras + 1
    flow = _AssignmentFlow(sink + 1)
    _connect_quotas(flow, range(first_target, extras), unit_count, quotas)

    # The target index sequence is a base-M number. It is strictly less than
    # the distance multiplier, so no tie-break can outweigh a distance step.
    base = target_count
    distance_weight = base ** unit_count
    place_value = distance_weight
    for unit, row in enumerate(distances):
        place_value //= base
        flow.connect(source, unit, 1)
        for index, distance in enumerate(row):
            cost = distance * distance_weight + index * place_value
            flow.connect(unit, first_target + index, 1, cost)

    for _ in distances:
        flow.send_one(source, sink)
    return [
        flow.target_used_by(unit, first_target) for unit in range(unit_count)
    ]


def _connect_quotas(
    flow: _AssignmentFlow, targets: range, unit_count: int,
    quotas: tuple[int, ...] | None,
) -> None:
    extras = targets.stop
    sink = extras + 1
    if quotas is not None:
        for target, quota in zip(targets, quotas, strict=True):
            flow.connect(target, sink, quota)
        return

    # Sending N units fills all base quotas and exactly r extra slots.
    quota, remainder = divmod(unit_count, len(targets))
    flow.connect(extras, sink, remainder)
    for target in targets:
        flow.connect(target, sink, quota)
        flow.connect(target, extras, 1)
