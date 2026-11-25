---
title: "02 - Nearest-objective scripted player"
date_created: 2026-11-25
tags: [design, scripted-player, movement]
---

# Nearest-objective scripted player

## 1. Purpose and scope

Replace the [no-op scripted player's](01-no-op-scripted-player.md) empty movement
policy with a one-turn policy: each living, deployed unit owned by the player
advances independently toward the objective nearest to its current hex.

This is the next thin slice of [issue #407](https://github.com/jhull123/battle-hexes/issues/407),
not its group-based design. There is no group assignment, objective balancing,
support behavior, multi-turn route planning, or tactical search. There are no
scenario-specific policies and no changes to the UI, PPO integration, scenario
definitions, or game rules.

## 2. Definitions

- **Objective hex:** A distinct `(row, column)` from `Board.get_objectives()`,
  resolved to a board hex using `Objective.coords`. Multiple objective records
  at one coordinate are one target. Objective points and type do not affect
  selection.
- **Hex distance:** `Board.hex_distance`, the unweighted distance on the hex
  grid. It ignores terrain, occupants, and the cost or existence of a legal route.
- **Full objective:** The chosen hex has exhausted the board's finite friendly
  stacking limit for the moving unit, counting earlier moves as described below.
  An enemy-occupied hex is blocked by the enemy-entry rule, not by friendly
  stacking. An unset stacking limit does not cap friendly occupancy.
- **Hold:** Return no plan for the unit, not a path containing only its start.

## 3. Requirements

### Per-unit target and destination

1. **REQ-001 — Select the target.** On each `movement()` call, read the current
   board. Consider only on-board units owned by the scripted player (use
   `Board.get_units_for_player`, not the historical list of known units).
   If there are no objective hexes, return `[]`. For each eligible unit, hold
   if it is already on any objective. Otherwise, choose the objective with the
   smallest `(hex distance from start, row, column)` tuple, in ascending order.
   Do not substitute a different objective because the chosen one is occupied,
   full, or unreachable. Do not remember a target between turns.
2. **REQ-002 — Find legal one-turn moves.** Use core terrain-aware reachability
   with `unit.current_turn_movement_points_remaining` and the planning occupancy
   below. Reuse core path construction and entry rules; the path must fit that
   same budget, respect stacking and enemy occupancy at every step, and not
   continue through a hex where core reachability stops movement because of
   enemy adjacency.
3. **REQ-003 — Advance or hold.** Enter the chosen objective if reachable.
   If it is full and the unit is already adjacent to it, hold even if another
   neighboring hex is reachable. If it is full and the unit is farther away,
   prefer a legal, reachable adjacent hex. Use the board's neighbor relation.
   If no such hex is reachable, or if the objective cannot be entered for
   another reason, choose the legal reachable destination with the smallest
   `(hex distance to target, row, column)` tuple among hexes strictly closer
   than the start. Use the same tie-break for adjacent candidates. If no
   qualifying destination exists, hold. Progress is measured at the endpoint;
   a legal one-turn path may detour, but the policy never issues an equal- or
   greater-distance move just to set up a future turn.

### Planning multiple units

4. **REQ-004 — Resolve conflicts in plan order.** Process units in ascending
   lexicographic order of `str(unit.get_id())`. Start from current occupancy in
   a private planning view. After accepting a plan, treat that unit as having
   left its origin and occupied its destination for all later plans. Holding
   and unprocessed units remain in place. Use this occupancy for both
   reachability and path construction, not just the destination check: once a
   hex fills, later units cannot end there or pass through it. Intermediate
   steps do not reserve capacity after a plan ends. Sharing a destination is
   legal when core permits the resulting stack. Return plans in the same order
   and do not rely on a later unit vacating a hex.
5. **CON-001 — Preserve core authority.** Do not mutate the live board or units
   while planning, persist reservations, or consume randomness. The projection
   assumes earlier plans finish as intended. Core applies plans in order,
   rechecks entry at each step, and resolves defensive fire. If actual
   positions differ, accept core's result without replanning within the batch.
   On the next movement turn, use actual positions and capacity from the
   current board. Core remains responsible for movement resolution, defensive
   fire, combat, scoring, and victory.

## 4. Interfaces and data contracts

- Keep the policy in `battle_agent_rl.scripted`. Extend `ScriptedPlayer` without
  changing `Player.movement()` or the stable `scripted` type ID, **Scripted
  Player** label, or `PlayerType.CPU` category. Bind each scripted player to the
  live board through the existing creation and saved-game hydration paths.
  The board reference is runtime wiring; no policy state, save migration, or
  schema change is required.
- `movement()` returns `list[UnitMovementPlan]`, at most one plan per moving
  unit. A plan references the actual game unit and contains a sequence of board
  `Hex` values, starting with its current hex and ending at the destination.
  Consecutive hexes are neighbors. Emit no plan for held units.
- Use the existing CPU movement command and phase flow. An empty list is a
  successful `plans: []` response, not a reason to skip end-of-movement,
  pending combat, scoring, victory checks, or the normal handoff when play
  continues. Keep callbacks unchanged.

## 5. Acceptance criteria

Coordinates below are `(row, column)`, indexed from zero. Unspecified terrain
costs one movement point per entry. Stacking is unlimited unless stated.

| Case | Given | Expected |
| --- | --- | --- |
| AC-001 — Independent choices | On a 6×1 board, objectives are at `(0, 0)` and `(5, 0)`. Units start at `(1, 0)`, `(2, 0)`, and `(4, 0)` with budgets of 1, 2, and 1 respectively. | The first two move to `(0, 0)` and the third to `(5, 0)`. The units do not balance assignments, and legal sharing is allowed. |
| AC-002 — Target tie | A unit at `(2, 0)` can reach objectives at `(1, 0)` and `(3, 0)` in one step. The latter has more points. | It enters `(1, 0)` regardless of objective enumeration order or point values. |
| AC-003 — Advance and hold on arrival | On a 6×1 board, a unit at `(0, 0)` has two movement points per turn and the sole objective is at `(5, 0)`. | Applying plans across successive turns yields `(2, 0)`, `(4, 0)`, and `(5, 0)`. On its next turn it issues no plan. |
| AC-004 — Terrain and remaining budget | On a 5×1 board, a unit at `(0, 0)` has a base allowance of four but only two points left. Entering `(1, 0)` costs two; the objective is at `(4, 0)`. | It ends at `(1, 0)`, not `(2, 0)` or farther. |
| AC-005 — Enemy blocks the target | On a 6×1 board, a unit at `(3, 0)` has three points. An enemy occupies the objective at `(5, 0)`; the other objective at `(0, 0)` is reachable. | Its plan ends at `(4, 0)`, not at the enemy or the farther objective. If core leaves it there and the enemy remains, it has no plan on its next turn. |
| AC-006 — Approach a full objective, wait, then enter | On a 5×5 board with limit two, two friendly units occupy the objective at `(2, 2)`. A mover at `(2, 0)` has one point per turn; another objective is at `(4, 4)`. Empty `(1, 1)` and `(2, 1)` are both reachable adjacent hexes. | The mover goes to `(1, 1)` by the destination tie-break. It holds on the next turn with the objective still full, even though it could move to `(2, 1)`. After core removes one occupant, it enters `(2, 2)` on its next movement turn if the step is legal. |
| AC-007 — Last adjacent slot | On a 5×1 board with limit two, the objective at `(4, 0)` has two friendly occupants and `(3, 0)` has one. Units `a` and `b` start at `(1, 0)` with two points each. | `a` claims the last slot at `(3, 0)`. `b` cannot reach a legal adjacent hex, so it advances to `(2, 0)`. Reversing board insertion order does not change the winner. |
| AC-008 — Contest the objective itself | On a 4×1 board with limit one, units `a` at `(0, 0)` and `b` at `(2, 0)` can both enter the empty objective at `(1, 0)`. | `a` enters first. The projected stack is then full, so adjacent `b` holds. |
| AC-009 — Transit and vacated capacity | On a 6×1 board with limit one, the objective is at `(5, 0)`. Unit `a` at `(2, 0)` has one point and unit `b` at `(1, 0)` has four. | `a` moves to `(3, 0)`. `b` may enter the vacated `(2, 0)`, but cannot traverse the now-full `(3, 0)`, so it stops at `(2, 0)`. Both plans apply in order without a stacking conflict. |
| AC-010 — Re-evaluate from the actual position | On a 9×1 board with objectives at `(0, 0)` and `(8, 0)`, a unit first moves from `(3, 0)` to `(2, 0)` with one point. Before its next turn, core leaves it at `(5, 0)` following other game resolution. | In the new board state with no intervening blockers and one point available, it moves to `(6, 0)` toward `(8, 0)`, not toward its old target. |
| AC-011 — No objectives | The board has no objectives and contains a scripted unit with a legal move. | The player returns `[]`; ordinary CPU phase commands resolve any pending combat and hand off the turn unless the game ends. |

## 6. Test automation strategy

- Use `pytest` policy tests with small core boards, real terrain and stacking,
  owned and unowned units, and a removed unit. Assert plan order, paths and
  destinations, absence of plans for ineligible or holding units, repeatability
  on unchanged inputs, and no live-state or randomness changes during planning.
- Apply representative batches through `Game.apply_movement_plans` to verify
  that the projected outcomes occur absent defensive fire and that the game
  result remains authoritative when movement is interrupted.
- Cover new and loaded scripted seats through the normal CPU command path.
  On an objective board, verify plans and resolved movement after hydration;
  on an objective-free board, retain coverage of normal phase flow with and
  without pending combat. Use `./server-side-checks.sh` for implementation
  validation; no new browser or performance suite is required.

## 7. Rationale and context

Distance selects the target even when terrain or congestion prevents immediate
entry. Minimizing the remaining distance among legal moves lets the unit advance
as far as this turn permits without requiring it to spend every movement point.
Stable coordinate and unit ordering make ties and contention reproducible.
Waiting beside a full objective prevents lateral shuffling without introducing
a persistent queue or group policy.

## 8. Dependencies and external integrations

This slice uses ordinary Python, the core board and movement interfaces, and
the existing scripted CPU creation, save/load, and command flow. It adds no
external services, infrastructure, or machine-learning runtime dependency.

## 9. Additional edge cases

- If a unit cannot get closer to a full objective and cannot reach an adjacent
  hex, it holds; the existence of a reachable farther objective does not change
  that decision.
- A friendly-occupied objective below its limit is not blocked by occupancy.
  If it becomes reachable on a later turn, a unit outside it can enter without
  waiting for it to empty.
- A hex that happens to contain another objective is ranked like any other
  candidate when approaching the chosen target. If the unit ends there, it
  holds on the next turn under the same on-objective rule.

## 10. Validation criteria

The increment is complete when AC-001 through AC-011 pass with core reachability
and the existing CPU command flow, and the policy still runs without machine
learning dependencies or changes to public contracts or core rules.

## 11. Related specifications and code

- [01 - No-op scripted player](01-no-op-scripted-player.md)
- [Core board and objective access](../../battle_hexes_core/src/battle_hexes_core/game/board.py)
- [Core reachability and paths](../../battle_hexes_core/src/battle_hexes_core/game/movement.py)
- [Core movement plan](../../battle_hexes_core/src/battle_hexes_core/game/unitmovementplan.py)

## Open Questions

No questions.
