---
title: "03 - Balanced objective assignment for the scripted player"
date_created: 2026-11-25
tags: [design, scripted-player, objectives, persistence]
---

# Balanced objective assignment for the scripted player

## 1. Purpose and scope

Replace the [nearest-objective policy](02-nearest-objective.md) with a fixed
objective assignment for each scripted unit. At creation, spread each scripted
side's units evenly by count, then minimize their total starting hex distance.
Assign later reinforcements without changing existing targets.

This increment changes target selection and adds the policy state needed to
retain it. Group tactics, dynamic rebalancing, new pathfinding or combat
behavior, scenario format changes, user interface changes, and PPO integration
are out of scope.

## 2. Definitions

- **Objective hex:** A distinct, valid `(row, column)` from
  `Board.get_objectives()` and `Objective.coords`. Multiple objective records on
  the same hex count once. Objective order is ascending numeric row, then
  ascending numeric column.
- **Living, deployed unit:** A unit currently on the board and owned by the
  scripted player, as returned by `Board.get_units_for_player`. This includes
  units with zero movement. Eliminated units and off-board reinforcements do
  not count. Unit order is ascending lexicographic `str(unit.get_id())`.
- **Hex distance:** The unweighted grid distance from `Board.hex_distance`,
  not the cost or length of a legal route.
- **Full objective:** Its finite friendly stacking capacity is exhausted in
  the movement planning view. Enemy occupancy blocks entry separately. An unset
  stacking limit does not cap a friendly stack.
- **Hold:** Issue no movement plan for the unit.

## 3. Requirements

### Starting assignments

1. **REQ-001 — Initialize each scripted side independently.** After core has
   placed the scenario's initial units and objectives and processed its
   turn-one reinforcement deployment, assign every living, deployed unit on
   each scripted side. Complete initialization before the new game is returned
   or first saved. Reinforcements already on the board at creation are part of
   this initial batch; blocked or future groups are not. A side with no units
   or a board with no objectives receives an empty assignment.
2. **REQ-002 — Balance by count before minimizing distance.** For `N` eligible
   units and `M > 0` objective hexes, assign each unit to exactly one hex.
   If `N = q × M + r` with `0 ≤ r < M`, exactly `r` objectives get `q + 1`
   units and the rest get `q`. The optimization chooses which objectives get
   the extra units. Among all balanced assignments, minimize the sum of the
   distances from each unit's starting hex to its target. Use a global optimum,
   not greedy nearest-available selection. Do not weight unit strength,
   objective points or type, terrain, roads, current occupancy, stacking
   capacity, or route feasibility. Even a unit starting on an objective can
   be assigned elsewhere.
3. **REQ-003 — Break global ties deterministically.** In unit order, form the
   sequence of assigned objective coordinates. Of the balanced assignments
   with the minimum total distance, choose the lexicographically smallest
   sequence under objective order. In other words, the first differing unit
   gets the earlier objective. Neither enumeration order nor randomness may
   affect the result.

### Assignment lifetime and later arrivals

4. **REQ-004 — Keep surviving assignments fixed.** Movement, displacement,
   objective control changes, congestion, and losses must not change any
   surviving unit's target. Eliminated units stop counting immediately.
   Compute reinforcement counts from living assigned units on the arriving
   unit's side, including units that are not at their target. Count every
   objective, including any with zero assigned units. Ignore the other side's
   assignments and all unassigned or off-board units.
5. **REQ-005 — Assign only successful arrivals, one unit at a time.** After
   creation, process successful groups in the core deployment order (scenario
   declaration order within a deployment pass), and process their units in
   unit order after the whole group has legally deployed. For each arriving
   scripted unit, choose the objective with the smallest ascending tuple
   `(living assigned count, hex distance from arrival hex, row, column)`. Add
   the assignment to the count before processing the next arrival. If there
   are no objectives, leave arrivals unassigned. Blocked attempts do not add
   assignments or counts; a group that succeeds on a retry is handled at
   actual arrival. Do not alter group deployment, move its entry hex, or
   reassign units that already have targets.

### Movement and turn flow

6. **REQ-006 — Use only the assigned target.** Hold if the unit is on its own
   assigned objective, not merely any objective. Otherwise, use its current
   position and remaining movement points with the existing legal one-turn
   planner. Enter the assigned hex if legally reachable. If it is full and the
   unit is adjacent, hold; if farther away, prefer a legal reachable adjacent
   hex. If none is reachable, or entry is blocked for another reason, choose
   a legal reachable endpoint strictly closer to the assigned hex, ranked by
   `(remaining hex distance, row, column)`. Use the same tie-break for
   adjacent destinations. Hold if no such move exists. On a later movement
   turn, enter when space opens and the move is legal. Never pick another
   target because it is nearer, free, or reachable.
7. **CON-001 — Preserve movement and combat rules.** Retain [spec 02's](02-nearest-objective.md)
   unit order, private sequential occupancy projection, legal path construction,
   and core resolution of movement, defensive fire, and combat. Earlier plans
   affect both the endpoints and traversable hexes of later plans. If core
   interrupts a plan, accept the actual outcome without replanning in the
   batch. Planning does not write assignments, mutate the live board, or
   consume randomness. With no objectives, return `[]` (`plans: []` over the
   existing command). Continue normal phase flow, including pending combat,
   scoring, victory checks, and handoff if the game remains in progress.

## 4. Interfaces and data contracts

### Lifecycle boundaries

- **Creation:** The API factory supplies `ScriptedPlayer` instances by the
  stable `scripted` type ID. Core `GameCreator.build_game_components` wires the
  board, puts units and objectives on it, and constructs `Game`, which attempts
  turn-one deployment. Use the completed starting board for REQ-001, not the
  player constructor or the first `movement()` call.
- **Reinforcements:** Later attempts run from `Game.next_player` when the turn
  number advances. Use the authoritative successful deployment and its actual
  units and entry hex, not the scheduled turn or reinforcement history (the
  history records unit counts, not unit IDs). Assign for either scripted side
  even if that side is not active, before the transition returns and its
  snapshot is committed. The reinforcement deployer remains responsible for
  placement. Core may expose a policy-neutral lifecycle hook or result; it
  must not import `ScriptedPlayer` or run the assignment policy itself.
- **Ownership:** The assignment policy belongs in `battle_agent_rl.scripted`.
  Persistence adapts the policy state; routes and HTTP schemas do not compute
  or expose it. Keep the `Scripted Player` label, `PlayerType.CPU` category,
  `Player.movement()` interface, and existing command and response contracts.

### Saved assignments

- **REQ-007 — Encode authoritative state.** Extend the internal version-1
  state document with `scripted_objective_assignments` for games with at least
  one scripted seat. Encode a list of records in unit order, each containing
  string `unit_id` and integer `row` and `column` of the target. Unit IDs are
  unique across the scenario, so derive ownership from existing unit/player
  data. Save one record per active scripted unit if there are objectives, or
  `[]` if there are no objectives or no active scripted units. Do not write
  eliminated units, pending reinforcements, or records for other player types.
  Omit this field entirely for games without scripted seats.
- **REQ-008 — Restore rather than recalculate.** When the field is present,
  validate that it is a list with exactly the required active unit IDs, no
  duplicates, and only valid objective coordinates. Reject invalid or
  incomplete data, including this field on a game without a scripted seat,
  via `SavedGameIncompatibleError`, not by reseeding. Do not validate current
  balance, distance optimality, or target occupancy; these may legitimately
  have changed since assignment. Restore the targets verbatim after
  `GameStateHydrator` has restored the saved board, units, and reinforcement
  state. Baseline construction must not supply or overwrite those targets.
- **REQ-009 — Load legacy documents deterministically.** If a version-1
  document has a scripted seat and the field is absent, initialize that seat
  once on the detached, fully restored board with REQ-002 and REQ-003. Use
  saved positions and living deployed units, including reinforcements already
  on the board; do not replay arrival history or assign pending units. This is
  policy initialization, not a game transition. Repeated reads of the same
  legacy snapshot produce the same assignments without a repository write or
  game-version change. Persist the assignments on the next successful
  command commit, along with any arrivals or losses in that command. A
  present empty list is not a legacy marker, and `null` is invalid. Old saves
  without scripted seats load as before.
- **CON-002 — Reuse the existing save transaction.** Creation and commands that
  deploy reinforcements store the resulting assignments with the same snapshot
  and receipt as the rest of the game state. Retry, replay, and version
  conflict handling remain unchanged. Hydration must not advance phases,
  replay reinforcement attempts against the restored board, or generate
  movement orders.

## 5. Acceptance criteria

Coordinates below are zero-based `(row, column)`. On one-column fixtures,
distance is the absolute row difference. Use plain terrain and unlimited
stacking unless otherwise specified.

| Case | Given / when | Expected |
| --- | --- | --- |
| AC-001 — Uneven counts | Objectives at rows `0`, `5`, `10`; five units start at rows `0`, `5`, `5`, `10`, `10`. Include two objective records at row `5`. | Counts in objective order are `1/2/2`, total distance is zero, and row `5` counts once. With two scripted seats, each side satisfies its own counts. |
| AC-002 — Fewer units than objectives | Same three objectives. Units `a` and `b` both start at row `8`. | Counts are `0/1/1`; `a` targets row `5`, `b` targets row `10`. Both cannot choose their nearest objective. |
| AC-003 — Globally shortest balanced assignment | Objectives at rows `0` and `10`. Unit `a` starts at row `4`; `b` at row `1`. | `a → 10`, `b → 0`, total distance `7`, instead of the greedy result `a → 0`, `b → 10` with total `13`. Changing strengths, points, terrain, or target occupancy without changing the eligible units or their starts does not change assignments. |
| AC-004 — Deterministic global tie | Objectives at rows `0` and `4`. Unit `a` starts at `4`; `b` at `5`. Both balanced assignments cost `5`. | `a → 0`, `b → 4` even if unit insertion or objective enumeration is reversed. Tie-breaking is over the full assignment, not each unit's nearest objective. |
| AC-005 — Reload without reshuffling | Objectives at rows `0` and `8`. At creation, `a` starts at `3` and is assigned `0`; `b` starts at `7` and is assigned `8`. Before saving, they are displaced to rows `7` and `1`, respectively. Reload with one point each and no blockers. | Saved targets remain `a → 0`, `b → 8`. The next plans end at rows `6` and `2`, respectively. A new balance from the restored positions would give the opposite targets. |
| AC-006 — Losses do not redistribute | Two objectives have two assigned units each. Core eliminates both assigned to the first objective; a survivor stands closer to the first than to its assigned second objective. | The living counts become `0/2`. Both survivors keep the second objective, including across a save/load round trip. |
| AC-007 — Multiple arrivals and all tie-breaks | Objectives `A/B/C` at rows `0/4/8` have living counts `2/1/0`. In the same deployment pass, the first group arrives at row `2` listing `r3, r2, r1`; the second arrives at row `6` with `r0`. | In order, `r1 → C` (fewest), `r2 → B` (nearer of `B/C`), `r3 → C` (fewest after `r2`), `r0 → B` (same distance to `B/C`, earlier coordinate). Counts end at `2/3/2`. The new targets are already saved when the transition commits, even if the arriving side is not active. |
| AC-008 — Turn-one arrivals and blocked retry | One group enters during construction, a second due group is blocked, and a third is not yet due. On a later turn, core can deploy the blocked group. | The initial optimum includes the first group at its entry hex and excludes both undeployed groups. The blocked group receives assignments only when its retry succeeds, using the living counts at that time. Replaying the successful command does not count the arrivals again. |
| AC-009 — Full objective | With stacking limit two, two friendly units fill the sole objective at `(2, 2)`. A third assigned unit starts at `(2, 0)` with one point per turn and can reach both `(1, 1)` and `(2, 1)`. | It advances to `(1, 1)` by coordinate tie-break, holds beside the full target, and enters on a later turn once a slot opens and entry is legal. On arrival it holds; no assignment changes. If no adjacent hex is legally reachable, it makes only legal strict progress or holds. |
| AC-010 — Non-target objective and enemy blocker | Two units on the same objective get different assignments. The unit assigned elsewhere can legally advance; later an enemy occupies that unit's target. | The unit leaves the non-target objective when able. It cannot enter the enemy-held hex and never switches targets, even if the other objective is reachable. |
| AC-011 — No objectives | A scripted side has legal moves and may receive reinforcements on a board with no objectives. | Save `[]` for assignments and return `plans: []` even after arrivals and reload. Normal phase commands resolve any pending combat and hand off unless the game ends. |
| AC-012 — Legacy upgrade and invalid state | Remove the field from a version-1 save with displaced units, previously arrived reinforcements, and pending groups. Separately test a present field with a duplicate ID, missing active unit, pending or non-scripted unit, non-objective coordinate, or `null`. | The absent field seeds a deterministic balanced assignment from the saved active units and positions. Reads do not write; the next successful command saves it. Invalid present data is rejected as incompatible and never triggers the fallback. |

## 6. Test automation strategy

- Use `pytest` policy tests with core boards and stable unit IDs. Compare the
  initial solver against exhaustive enumeration on small fixtures to check
  balance, total distance, and the complete tie-break. The production solver
  should use an exact method that scales beyond exhaustive enumeration, such
  as minimum-cost assignment with lower and upper objective quotas.
- Exercise the actual creation and turn-transition paths for arrivals, blocked
  retries, and multi-seat behavior. Verify assignments before the first
  movement call and after successful commits. Test codec round trips and
  legacy and malformed documents separately from movement.
- Keep spec 02's legal movement, stacking, and defensive-fire regressions.
  Update only cases that assert obsolete target choice. Use the existing CPU
  commands for objective-free phase flow and run `./server-side-checks.sh`
  when implementing. No new browser suite is needed.

## 7. Rationale and context

Balancing by count spreads a side across objectives without introducing unit
roles or coordinated tactics. The global minimum avoids needless travel
within that constraint. Fixed assignments prevent retreat, congestion, or
casualties from shifting the whole side's targets. New arrivals can fill gaps
without diverting units already moving toward an objective.

## 8. Dependencies and external integrations

Use the core board, movement, and deployment interfaces, the scripted player
package, and the existing authoritative game-state codec and command service.
No external service, infrastructure change, new scenario field, or
machine-learning dependency is required.

## 9. Additional edge cases

- A unit with zero movement still counts toward balance and reinforcement
  selection. It holds when it has no legal progress.
- A scripted side can start with no deployed units. Its first successful later
  arrival sees zero counts at all objectives and chooses by arrival distance,
  then objective order.
- A target can have more assigned units than its stacking limit permits on the
  hex. Assignment is not a reservation; waiting and entry depend only on legal
  movement and projected occupancy.

## 10. Validation criteria

The increment is complete when AC-001 through AC-012 pass, surviving targets
are stable across save/load and turn transitions, and existing movement,
combat, and CPU command regressions pass without public contract changes.

## 11. Related specifications and code

- [01 - No-op scripted player](01-no-op-scripted-player.md)
- [02 - Nearest-objective scripted player](02-nearest-objective.md) (movement
  rules retained; per-turn target selection and stateless saves superseded)
- [Core game creation](../../battle_hexes_core/src/battle_hexes_core/gamecreator/gamecreator.py)
- [Reinforcement deployment](../../battle_hexes_core/src/battle_hexes_core/game/reinforcements_deployer.py)
- [Game-state codec](../../battle_hexes_api/src/battle_hexes_api/persistence/game_state_codec.py)
- [Game-state hydration](../../battle_hexes_api/src/battle_hexes_api/persistence/game_state_hydrator.py)

## Open Questions

No questions.
