# battle_hexes_core/vision.py
"""
Team-aware Fog of War and Line-of-Sight for axial hex grids.

Works with axial coordinates (q, r).
Provide your own `is_opaque((q, r)) -> bool` to mark blocking tiles
(e.g., walls, tall cliffs, smoke), and optional `in_bounds((q, r)) -> bool`
to constrain to your map.

Typical use:
    fov = compute_fov(origin=(q, r), radius=6, is_opaque=is_wall)
    vis.update_team(team_id=1, visible_now=fov)
    if vis.is_visible(1, target_hex): ...

This module is intentionally dependency-free and small enough to drop in.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Deque
from collections import deque
import math

Hex = Tuple[int, int]  # axial (q, r)

# --- Hex axial geometry helpers ------------------------------------------------

# axial directions (pointy-topped or flat-topped axial works the same for neighbors)
HEX_DIRECTIONS: List[Hex] = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1),
]

def hex_add(a: Hex, b: Hex) -> Hex:
    return (a[0] + b[0], a[1] + b[1])

def hex_neighbor(h: Hex, direction: int) -> Hex:
    dq, dr = HEX_DIRECTIONS[direction % 6]
    return (h[0] + dq, h[1] + dr)

def axial_to_cube(h: Hex) -> Tuple[int, int, int]:
    q, r = h
    x = q
    z = r
    y = -x - z
    return x, y, z

def cube_to_axial(c: Tuple[int, int, int]) -> Hex:
    x, y, z = c
    return (x, z)

def hex_distance(a: Hex, b: Hex) -> int:
    ax, ay, az = axial_to_cube(a)
    bx, by, bz = axial_to_cube(b)
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))

def hex_ring(center: Hex, radius: int) -> List[Hex]:
    """
    Returns hexes at exact distance == radius from center.
    """
    if radius <= 0:
        return []
    results: List[Hex] = []
    # start at "west-northwest" side: center + dir(4) * radius
    q, r = center
    cq, cr = q, r
    dq, dr = HEX_DIRECTIONS[4]
    cq += dq * radius
    cr += dr * radius
    # walk around 6 sides
    for side in range(6):
        ddir = HEX_DIRECTIONS[side]
        for _ in range(radius):
            results.append((cq, cr))
            cq += ddir[0]
            cr += ddir[1]
    return results

def hex_disk(center: Hex, radius: int) -> List[Hex]:
    """
    Returns hexes with distance <= radius (spiral).
    """
    out = [center]
    for r in range(1, radius + 1):
        out.extend(hex_ring(center, r))
    return out

# --- Hex line (for LoS) --------------------------------------------------------

def _cube_lerp(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[float, float, float]:
    ax, ay, az = a
    bx, by, bz = b
    return (ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t)

def _cube_round(frac: Tuple[float, float, float]) -> Tuple[int, int, int]:
    x, y, z = frac
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return int(rx), int(ry), int(rz)

def hex_line(a: Hex, b: Hex) -> List[Hex]:
    """
    Returns all hexes on the straight line from a to b, inclusive.
    """
    n = hex_distance(a, b)
    if n == 0:
        return [a]
    ca = axial_to_cube(a)
    cb = axial_to_cube(b)
    results: List[Hex] = []
    for i in range(n + 1):
        t = 0.0 if n == 0 else i / float(n)
        c = _cube_round(_cube_lerp(ca, cb, t))
        results.append(cube_to_axial(c))
    return results

# --- Visibility / LoS ----------------------------------------------------------

def line_of_sight(a: Hex, b: Hex, is_opaque: Callable[[Hex], bool]) -> bool:
    """
    True if the line from a -> b has no opaque hex in between a and b.
    The last hex (b) being opaque still counts as *visible* (you can see the wall).
    """
    cells = hex_line(a, b)
    if len(cells) <= 2:
        return True
    for h in cells[1:-1]:  # ignore `a` (start) and `b` (target)
        if is_opaque(h):
            return False
    return True

def compute_fov(
    origin: Hex,
    radius: int,
    is_opaque: Callable[[Hex], bool],
    *,
    in_bounds: Optional[Callable[[Hex], bool]] = None
) -> Set[Hex]:
    """
    Breadth-first FOV: visible set within radius; propagation halts at opaque tiles.
    This approximates realistic vision without per-ray checks. For small boards,
    ray-based FOV via `line_of_sight` + `hex_disk` is also viable.

    Returns a *set* of hexes currently visible.
    """
    visible: Set[Hex] = set()
    q: Deque[Tuple[Hex, int]] = deque()
    q.append((origin, 0))
    visible.add(origin)

    while q:
        h, d = q.popleft()
        if d >= radius:
            continue

        for dir_idx in range(6):
            n = hex_neighbor(h, dir_idx)
            if n in visible:
                continue
            if in_bounds and not in_bounds(n):
                continue

            # The neighbor itself is visible, but if it's opaque, do not expand beyond
            visible.add(n)
            if not is_opaque(n):
                q.append((n, d + 1))

    return visible

# --- Team Fog-of-War -----------------------------------------------------------

@dataclass
class TeamVision:
    # hexes seen this turn (ephemeral)
    visible_now: Set[Hex] = field(default_factory=set)
    # hexes seen at least once (persistent)
    revealed: Set[Hex] = field(default_factory=set)

class FogOfWar:
    """
    Tracks per-team visibility: 'visible now' and 'ever revealed'.
    Call `update_team` each turn with the set of hexes currently visible to that team.
    """
    def __init__(self) -> None:
        self._teams: Dict[int, TeamVision] = {}

    def ensure(self, team_id: int) -> TeamVision:
        tv = self._teams.get(team_id)
        if tv is None:
            tv = TeamVision()
            self._teams[team_id] = tv
        return tv

    def update_team(self, team_id: int, visible_now: Iterable[Hex]) -> None:
        tv = self.ensure(team_id)
        vis = set(visible_now)
        tv.visible_now = vis
        tv.revealed |= vis

    def is_visible(self, team_id: int, h: Hex) -> bool:
        tv = self.ensure(team_id)
        return h in tv.visible_now

    def is_revealed(self, team_id: int, h: Hex) -> bool:
        tv = self.ensure(team_id)
        return h in tv.revealed

    def clear_turn(self, team_id: Optional[int] = None) -> None:
        """
        Optional: clear 'visible_now' between turns.
        If team_id is None, clears all teams.
        """
        if team_id is None:
            for tv in self._teams.values():
                tv.visible_now.clear()
        else:
            self.ensure(team_id).visible_now.clear()
