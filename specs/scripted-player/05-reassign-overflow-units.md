---
title: "05 - Reassign overflow units for the scripted player"
date_created: 2026-11-25
tags: [design, scripted-player, objectives, persistence]
---

# Reassign overflow units for the scripted player

## 1. Purpose and scope

Let a concentrated opening become a second push. A `6/0/0` assignment stays
intact until the assigned objective is held and full at the start of the side’s
movement phase. Then the units that cannot fit redirect immediately, even if
they are still several hexes away.

This is the only exception to the fixed-target rules in specs 03 and 04.
Initial quota sampling and assignment, reinforcement assignment, movement
legality, defensive fire, combat, and scoring are unchanged. No
casualty-triggered redistribution, tactical search, UI changes, or PPO
(Proximal Policy Optimization) wiring are in scope.

## 2. Definitions

- **Objective:** A distinct valid hex from `Board.get_objectives()`. Deduplicate
  coordinates and order them by ascending numeric `(row, column)`.
- **Living, deployed unit:** A unit currently on the board and owned by the
  scripted side (`Board.get_units_for_player`), including units with zero
  movement remaining. Exclude eliminated units and undeployed reinforcements.
  Order units by ascending lexicographic `str(unit.get_id())`.
- **Held by the side:** At least one occupant of the objective hex belongs to
  the side and none belongs to an opponent. Use `Board.get_units_at` and
  player ownership, not score, assignment, or nearby units. An empty,
  enemy-occupied, or mixed-occupancy hex is not held by the side.
- **Full:** `Board.stacking_limit` is finite and the number of the side’s
  occupants on the hex is at least that limit. Count occupants whether or
  not they are assigned there. A `None` limit is unlimited and never full.
- **Living assignee count:** Number of the side’s living, deployed units
  currently assigned to an objective, whether or not they occupy it. Include
  objectives with zero assignees. This count ranks destinations; it is not
  occupancy or a stacking reservation.

## 3. Requirements

- **REQ-001 — Evaluate once before movement.** At the start of the active
  scripted side’s movement phase, after any due deployment and reinforcement
  assignment, take the live board’s positions and occupancy as the basis for
  the entire pass. Complete the pass before generating the side’s movement
  plans or applying any movement in that phase. Do not use the planner’s
  projected board, expected arrivals, or assignment counts to decide whether
  a hex is held or full. Being contested, enemy-held, or blocked is not a
  substitute for being held and full.
- **REQ-002 — Identify overflow from the starting assignments.** A unit is
  eligible if it is living and deployed, its assigned objective is held and
  full, and its current hex is not that objective. No adjacency, remaining
  movement, or reachability test applies. Units on their assigned objective
  keep that target and continue to hold under the existing planner.
- **REQ-003 — Choose and count redirects in unit order.** Process all eligible
  units in one ascending unit-ID order, even if their source objectives differ.
  For each, consider all different objectives the side does not hold at phase
  start. Minimize `(living assignee count, hex distance from the unit’s
  current hex, row, column)` using `Board.hex_distance`, not route cost.
  An enemy-held objective may be a destination; it is not a qualifying
  source. Do not filter destinations for route feasibility, terrain, or
  enemy occupancy. On a redirect, decrement the old target’s count and
  increment the new target’s count before considering the next unit. If no
  alternative qualifies, keep the current assignment. Do not recompute
  eligibility or apply another pass after moves, retreats, or losses.
- **REQ-004 — Use and retain the new target.** Replace the stored target
  before the existing planner runs that turn. Keep its legal advance-or-hold
  behavior and private sequential occupancy projection; a redirect does not
  guarantee a move or permission to enter the target. Retain the target if
  the unit cannot move or if a slot opens at its old objective. On a future
  phase, its then-current assignment can change only by the same held-and-full
  rule. A loss can affect occupancy and counts at the next check, but never
  triggers a pass by itself. Overflow selection uses no randomness.

## 4. Turn and save contracts

### Authoritative movement boundary

`POST /games/{game_id}/movement` currently uses `MovementAdapter` to call
`Player.movement()` and apply the returned plans. It can commit without
closing `current_phase == "movement"`; `/end-movement` is a separate command.
A receipt prevents replay of the same command, but not a second command
with a new key during the same phase.

- **REQ-005 — Guard phase preparation.** Use a shared, policy-neutral core
  preparation step for the current player in an in-progress movement phase.
  The scripted policy in `battle_agent_rl.scripted` owns the reassignment;
  core provides the lifecycle boundary without importing `ScriptedPlayer`.
  The authoritative generated-movement path and the ordinary in-process
  `GamePlayer` runner prepare before calling `Player.movement()`. Any other
  authoritative movement application in the active phase, including an empty
  batch when closing movement, must pass the same guard before applying moves.
  Prepare only once, even if the pass finds no eligible units or produces no
  plans. Keep `Player.movement()` itself free of assignment writes so calling
  it for a preview cannot consume the pass. Non-scripted players are unchanged.
- A new phase is pending at game start and on handoff to the next player
  (including a seat change within the same round). Do not run the check during
  creation or handoff: the first authoritative movement action executes it
  against the starting board, before any movement. Clear the completed
  marker on leaving movement, handoff, or game completion. Do not use
  `turn_number` alone as a guard: both seats can move in the same round.

### Snapshot and receipt

- **REQ-006 — Persist targets and the phase guard together.** Keep the
  version-1 `scripted_objective_assignments` list of `{unit_id, row, column}`
  records in string unit-ID order. It stores the resulting target for each
  living, deployed scripted unit when objectives exist, not original targets,
  quota history, or eliminated units. Add an internal optional boolean
  `scripted_overflow_evaluated` for the current scripted movement phase:
  `false` before preparation, `true` afterward, even for a no-op pass.
  Encode it for an active scripted movement phase only; omit it otherwise.
  When present, validate that it is a boolean and belongs to an in-progress
  scripted movement phase. No public request or response fields change.
- **REQ-007 — Restore without running the policy.** Hydrate the board,
  current seat, phase, targets, and marker verbatim. Do not validate targets
  against quotas or current occupancy. Hydration and read-only requests
  do not evaluate overflow, generate plans, write a snapshot, or change the
  version. Missing marker in an older snapshot means no overflow pass has
  been recorded; the first authoritative movement action in an active
  scripted movement phase runs it. Keep specs 03 and 04’s deterministic
  fallback for an absent assignment list and rejection of invalid present
  data. Do not resample a saved opening.
- **REQ-008 — Commit once.** Run preparation on `GameCommandService`’s detached
  command candidate. Commit the targets, phase marker (if still in movement),
  resolved board, and receipt atomically under the existing expected-version
  check. An uncommitted or losing candidate cannot change saved targets or mark
  the phase prepared. A matching receipt, including one found after an
  ambiguous commit, returns the original response without running the policy
  or applying moves again. A fresh command in an already prepared phase uses
  the saved targets without reevaluating overflow. Existing version-conflict
  and idempotency behavior stays unchanged.

## 5. Acceptance criteria

For the one-column fixtures below, a row number denotes `(row, 0)`. Use
controlled board states and legal movement; do not depend on random combat
outcomes or hunt for an opening seed.

| Case | Given / when | Expected |
| --- | --- | --- |
| AC-001 — Crossroads before the stack is full | Force `6/0/0` for the six Airborne units on `d_day_crossroads`. The objective at `(2, 3)` is empty or has one Airborne occupant when the phase begins. In the one-occupant case, let a movement plan put a second unit there. | All six assignments stay at `(2, 3)` for the phase, including after the move fills the stack. Plans respect capacity two. |
| AC-002 — Crossroads overflow | At the next Airborne phase, two of the six assigned units are still at `(2, 3)`; four are off the objective, including units several hexes away. Neither `(3, 15)` nor `(6, 9)` is Airborne-held. | The two holders retain their assignments and issue no move. All four overflow units change targets before plans are generated, yielding `2/2/2` by assignment count. Plans use the new targets immediately and still cannot enter enemy-occupied hexes. |
| AC-003 — Counts, order, and ties | Capacity two; two assigned holders fill objective `A` at row `0`. Other objectives `B` and `C` at rows `4` and `8` start empty with zero assignees. Off-target units `a`, `b`, `c`, `d` all target `A` and start at rows `6`, `5`, `7`, `7`, respectively. Reverse board and objective enumeration in a second run. | `a → B` on the coordinate tie; `b → C` on lower count despite `B` being nearer; `c → C` on distance with counts tied; `d → B` on lower count despite `C` being nearer. Both runs finish `2/2/2` with the same unit-to-target map. |
| AC-004 — No eligible destination | The source is held and full. It is the only objective, or all other objectives are held by the side (including one with free slots and no assignees). | No assignments change. The existing planner still advances legally or holds toward the original target. |
| AC-005 — Unlimited or blocked | With no stacking limit, place several friendly units on the assigned objective and leave others en route. Separately use a finite limit with a vacant slot and a route blocked for another reason. | Neither case redirects overflow. |
| AC-006 — Enemy or contested source | With limit two, put two enemy units on the assigned objective. In a separate synthetic fixture, give the objective mixed friendly and opposing occupants. Also test a held, full source whose only alternative is enemy-held. | Neither enemy nor mixed occupancy makes the original target qualify as a source. The enemy-held alternative in the last fixture is selected, but entry remains illegal while enemy units occupy it. |
| AC-007 — New target that turn; no recall | With a full friendly source at row `0`, put a displaced assignee at row `1` with one movement point and the only alternative at row `4` on plain terrain. Include a second off-target assignee with zero movement. Later vacate a slot at row `0`. | The mobile unit plans to row `2` in the redirecting phase. The zero-movement unit also changes target but issues no plan. Both retain row `4` as their target after the slot opens. |
| AC-008 — Save/load before and after the pass | Save a pending phase with a qualifying source. Reload, submit movement, then reload the committed snapshot while still in movement. Also read a legacy snapshot without the marker. | Loading alone changes no targets or version. The first authoritative movement request evaluates a pending phase. After commit, the redirected targets and prepared marker restore together. Legacy reads are side-effect free. |
| AC-009 — Same-phase retry and replay | Commit a movement command whose start-of-phase pass finds a slot open but whose moves fill it. Restart, replay with the same idempotency key and original expected version, then send a new movement command with a fresh key and current version while the phase is still open. | Replay returns the original receipt and does not change the version, board, or assignments. The new request cannot redirect the overflow in that same phase, even though the hex is now full. The next eligible phase can redirect it if it is still full. |
| AC-010 — Seat handoff and conflicts | In a two-scripted-side game, prepare the first seat, then hand off to the second in the same round. Exercise matching concurrent commits and a stale command on the movement path. | Only the active seat is evaluated at each phase start. The second seat gets its own pass. Only the authoritative commit changes the board, targets, and marker; a matching duplicate replays, and a stale non-replay command cannot overwrite the snapshot. |

## 6. Test automation strategy

Use `pytest` policy fixtures for the full assignment maps and movement plans.
Use the actual command service, repository, and codec to test phase boundaries,
round trips, retries, and conflicts. Include no-objective and no-deployed-unit
regressions: no redirects, normal phase flow. Keep the opening and reinforcement
tests, updating assertions that require permanent targets only where the new
trigger applies. No new browser suite or training run is needed.

## 7. Rationale

Occupancy answers whether the first push has filled its objective; assignment
counts only distribute the second push. Separating these checks lets distant
units turn early without diverting units while there is still room at their
assigned objective.

## 8. Dependencies and external integrations

Use existing board queries, movement rules, and command transactions. No
external service, new dependency, or scenario data change is required.

## 9. Examples and edge cases

- If one of two friendly occupants of a full objective is assigned elsewhere,
  both occupants still count toward fullness. The unit assigned elsewhere
  keeps its own target and may move under the existing planner. Do not
  anticipate its departure when deciding which other units to redirect.
- An unheld objective can have several living assignees still en route.
  They count when ranking that destination, but they do not make it held
  or full. A redirect can target that objective even if its living assignee
  count already exceeds its stacking limit.

## 10. Validation criteria

Implementation is complete when AC-001 through AC-010 and
`./server-side-checks.sh` pass, with no change to public commands or schemas.

## 11. Related specifications and code

- [03 - Balanced objective assignment](03-balanced-objective-assignment.md)
- [04 - Randomized objective splits](04-randomized-objective-splits.md)
- [Scripted player](../../battle_agent_rl/src/battle_agent_rl/scripted/scripted.py)
- [Core game lifecycle](../../battle_hexes_core/src/battle_hexes_core/game/game.py)
  and [movement command adapter](../../battle_hexes_api/src/battle_hexes_api/command_adapters/movement.py)
- [Command service](../../battle_hexes_api/src/battle_hexes_api/persistence/command_service.py)
  and [game-state codec](../../battle_hexes_api/src/battle_hexes_api/persistence/game_state_codec.py)
- [Crossroads on D-Day scenario](../../battle_hexes_core/src/battle_hexes_core/scenarios/d_day_crossroads.json)

## Open Questions

No questions.
