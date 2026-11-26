---
title: "04 - Randomized objective splits for the scripted player"
date_created: 2026-11-25
tags: [design, scripted-player, objectives, persistence]
---

# Randomized objective splits for the scripted player

## 1. Purpose and scope

Give Proximal Policy Optimization (PPO) a future opponent with varied but
purposeful openings. Randomize **how many** units target each objective, then
choose **which** units go there by minimizing total starting hex distance.
Keep [spec 03's deterministic balanced policy](03-balanced-objective-assignment.md)
as a selectable baseline and the default for callers that do not opt in.

This increment changes only how initial scripted targets are selected. It
does not add uncovered-objective reassignment, seek-and-destroy behavior,
movement or combat rules, scenario fields, user interface changes, or PPO
opponent wiring, training, or evaluation changes.

## 2. Definitions

- **Eligible unit:** A living, deployed unit owned by the scripted side,
  including units with zero movement. Sort by `str(unit.get_id())` in ascending
  lexicographic order. Eliminated units and undeployed reinforcements do not count.
- **Objective:** A distinct valid objective hex, regardless of how many
  objective records it holds. Sort by ascending numeric `(row, column)`.
- **Ordered quota vector:** For `N` eligible units and `M > 0` objectives, an
  `M`-tuple of nonnegative integers that sums to `N`. Entry `i` is the exact
  number of units targeting objective `i` in objective order. Permutations
  count as different splits when their vectors differ.
- **Balanced family:** If `N = q × M + r`, exactly `r` entries are `q + 1`
  and the others are `q`. The **unbalanced family** is every other valid
  vector. A zero quota is valid in either family.

## 3. Requirements, constraints, and guidelines

### Initial selection

- **REQ-001 — Initialize once per scripted side.** Use the completed starting
  board, after core places initial units and objectives and attempts turn-one
  reinforcement deployment, but before the game is returned or first saved.
  Include successful turn-one arrivals; exclude blocked and future groups.
  In randomized mode, select one vector for each scripted side from its own
  eligible count. Do not pool units or share a sampled vector across sides.
- **REQ-002 — Sample uniformly within each family.** Let `p` be the configured
  balanced probability, default `0.5`. When both families exist, choose the
  balanced family with probability `p` and the unbalanced family with
  probability `1 - p`. Then choose uniformly among the **ordered vectors** in
  the selected family. If only one family exists, give it all the probability
  regardless of `p`; do not retry or sample a family that cannot be used.
  Do not generate quotas by drawing independent targets for units, weighting
  by the number of unit assignments, or sampling an unordered split first.
- **REQ-003 — Handle degenerate inputs.** One objective yields `(N,)`; no
  units and `M > 0` yields the all-zero vector. Neither case needs a random
  draw. With no objectives, skip quota selection and assignment altogether.
  Return no scripted movement orders (`plans: []` over the existing command)
  and preserve ordinary phase flow.
- **REQ-004 — Solve the exact quotas globally.** Assign each eligible unit to
  one objective, filling every sampled quota exactly. Minimize the sum of
  `Board.hex_distance` from each unit's starting hex to its target. Among
  equally good assignments, choose the lexicographically smallest sequence
  of target coordinates in unit order, as in spec 03. Do not assign greedily
  or use more randomness to choose individual targets or break ties. Do not
  filter or weight objectives by occupancy, stacking, route feasibility,
  terrain, or points; do not weight units by strength or movement.
  The existing minimum-cost flow can use each exact quota as an objective's
  sink capacity: sending all `N` units saturates every quota, including
  leaving zero-quota objectives unused.
- **REQ-005 — Preserve the deterministic baseline.** In deterministic mode,
  use spec 03's global optimum across **all** balanced vectors, with the same
  tie-break and no opening randomness. Randomized mode with `p = 1` is not
  this baseline: when there are several balanced vectors it samples one
  without considering distance, then optimizes within that vector.

### Assignment lifetime

- **REQ-006 — Do not reroll.** Movement, retreat, loss, control changes, full or
  blocked objectives, later arrivals, reload, and command replay do not change
  a surviving unit's target. The initial quotas are not live targets to
  maintain. Keep spec 03's legal advance-or-hold behavior: an assignment is
  neither a stacking reservation nor permission to enter an illegal hex.
- **REQ-007 — Keep the reinforcement rule.** After creation, assign successful
  arrivals in core deployment order, and within each group in unit order.
  Choose the minimum `(living assigned count, hex distance from actual entry
  hex, row, column)` across every objective, updating the count after each
  unit. Count only living assigned units of the arriving side, whether or not
  they are at their targets. An objective with zero starting quota is still
  eligible; blocked arrivals are handled only when they actually deploy. No
  objectives means no assignment for arrivals.

## 4. Interfaces and data contracts

### Creation configuration and seed

Expose a Python-only opening configuration for fresh scripted players and
allow callers of the API's internal `GameCreator.create_sample_game` factory
to pass it through to the scripted seats before core starts the game. The
logical inputs are:

| Input | Default | Contract |
| --- | --- | --- |
| `mode` | `deterministic` | `deterministic` uses spec 03; `randomized` enables REQ-002. Reject unknown modes. |
| `balanced_probability` | `0.5` | Finite Python `int` or `float` in `[0, 1]`, inclusive (not a boolean). Reject invalid values rather than clamping. Used only in randomized mode. |
| `seed` | `None` | Optional integer (not a boolean); zero is an explicit seed. Used only in randomized mode. |

- **REQ-008 — Use separate, reproducible opening randomness.** Use one root
  seed per fresh randomized game. When no seed is supplied and randomness is
  needed, obtain a root seed from system entropy, not the shared game random
  source. Derive a private stream for each randomized seat from the SHA-256
  digest of the ASCII string `battle-hexes:scripted-opening:v1:<seed>:<seat>`.
  Use the decimal seed and the zero-based seat index in core player order;
  interpret the digest as an unsigned big-endian integer to seed a fresh
  Python `random.Random` instance. Use that instance only for opening quota
  selection. Never seed or draw from the process-wide generator or a game,
  combat, or defensive-fire random source. Other seats' sampling, game IDs,
  and prior games must not affect a seat's opening.
- With the same explicit seed, opening configuration, seat, eligible unit IDs
  and starting positions, and objective coordinates, a fresh game reproduces
  the same quotas and unit-to-target map under the same sampler and Python
  runtime. This is an opening guarantee, not a guarantee of identical combat
  or whole-game outcomes. Saves do not depend on regenerating a seeded opening
  after a runtime or sampler change.
- Use the existing policy-neutral `game_started_cb` to read the completed
  board. The sampler and assignment solver belong in `battle_agent_rl.scripted`,
  not in core, routes, or schemas. Keep `scripted`, the CPU player category, the
  public HTTP requests and responses, and the movement command unchanged.

### Sampling contract

For `M > 0`, the total number of vectors is `C(N + M - 1, M - 1)` and the
balanced count is `C(M, r)`, where `C(a, b)` is the binomial coefficient. The
unbalanced count is the difference. A vector's unconditional probability is
`p / balanced_count` or `(1 - p) / unbalanced_count` when both families exist.
If only one exists, each vector in it has probability `1 / family_count`.

Use an unbiased bounded-integer draw for the family choice: for configured
`p = a / b` (the exact ratio of the accepted numeric value), draw in `[0, b)`
and choose balanced iff the draw is less than `a`. Skip this draw when the
family is forced by availability or by `p = 0` or `p = 1`. Within the chosen
family, draw an unbiased integer rank in `[0, family_count)` and select the
vector at that rank in ascending lexicographic order. A singleton uses rank
zero without a draw. Prefer combinatorial counting and rank selection that
does not materialize all splits as counts grow; do not repeatedly sample and
discard vectors from the wrong family.

### Save, load, and replay

- **REQ-009 — Save the assignments, not the draw.** Reuse version 1's
  `scripted_objective_assignments`: one `{unit_id, row, column}` record per
  living, deployed scripted unit when objectives exist, sorted by string
  `unit_id`. Use `[]` when there are scripted seats but no such assignments;
  omit the field for games without scripted seats. Do not persist the mode,
  seed, generator state, or initial quotas; the saved targets are authoritative.
- **REQ-010 — Restore or fall back without sampling.** Keep hydration's
  `initialize_players=False` path. After restoring the saved board, units,
  and reinforcement state, restore a valid present assignment list verbatim.
  Keep spec 03's validation of IDs and coordinates, not of current balance,
  distance optimality, or occupancy. Invalid present data (including `null`)
  is incompatible; a valid present `[]` is not a legacy marker. For a legacy
  save with scripted seats and the field **absent**, use the deterministic
  baseline on the fully restored board, regardless of the fresh-game opening
  configuration. Repeated legacy reads do not write or change the version;
  the next successful command saves the resulting targets.
- **REQ-011 — Keep the existing command transaction.** Commit targets with the
  same snapshot and receipt as creation or a later successful command. Replay
  an existing receipt without running opening initialization or reapplying
  arrivals. If concurrent creation attempts build separate candidates, the
  committed snapshot and receipt are authoritative; a losing candidate must
  not replace the committed targets. Retry and version conflict behavior is
  otherwise unchanged.

## 5. Acceptance criteria

One-column fixtures below use row numbers as shorthand for `(row, 0)`.

| Case | Given / when | Expected |
| --- | --- | --- |
| AC-001 — Crossroads distribution | Create a randomized Airborne side on `d_day_crossroads` with default `p`. | The six eligible units and three ordered objectives yield 28 vectors. `2/2/2` has probability `1/2`; each of the other 27 has `1/54`. |
| AC-002 — Crossroads all-in | Force each of `6/0/0`, `0/6/0`, and `0/0/6` in separate games. | All six units have the selected objective as their target before the first move, and each opening is distinct. Plans obey the scenario's stacking limit of two and normal entry rules, even when the target is full or enemy-held. Units advance legally or hold without switching targets. |
| AC-003 — Uneven counts and configuration | Use five units and three objectives; exercise default `p`, `p = 0`, and `p = 1`. | `2/2/1`, `2/1/2`, and `1/2/2` each have probability `p/3`; each of the 18 unbalanced vectors has `(1-p)/18`. At the endpoints only the chosen family has support. |
| AC-004 — One objective or one family | Use one objective with `N > 0` at `p = 0`; separately use one unit and three objectives at `p = 0`. | The sole objective gets all `N` units without a draw. With one unit and three objectives, the three singleton placements are all balanced and equally likely, with no family draw or retry. |
| AC-005 — No units or no objectives | Use a scripted side with no eligible units and three objectives; separately use a side with deployed units and no objectives. | The first vector is `0/0/0`; the second case has no vector. Neither consumes opening randomness. Both save `[]` and yield no movement orders; with no objectives, later arrivals remain unassigned and normal phase flow continues. |
| AC-006 — Exact quotas and global optimum | Force `1/2` with objectives at rows `0` and `10` and units `a`, `b`, `c` at rows `4`, `1`, `9`. Separately force `1/2` with objectives at `0` and `4` and starts `4`, `5`, `6`. | First fixture: `a → 10`, `b → 0`, `c → 10`, total distance `8`; greedy assignment in unit order costs `14`. Second fixture: all feasible maps cost `7`; choose `a → 0`, `b → 4`, `c → 4`, even if units and objectives were enumerated in reverse. |
| AC-007 — Seed and lifecycle | Create the same game twice with an explicit seed (including seed `0`), distinct game IDs, and different shared random states. Exercise two scripted seats, plus a turn-one deployment fixture with a successful arrival, a blocked group, and a future group. | Each corresponding seat has identical quotas and assignments across runs and uses a separate stream; changing the other seat's opening draws does not change its result. Quotas include the successful arrival but exclude both undeployed groups. Opening initialization leaves shared and combat/defensive-fire randomness untouched. |
| AC-008 — Reload, replay, and loss | Save a forced all-in opening, then displace or eliminate units and block the target. Load saved snapshots with opening draws disabled, and replay a committed creation and a later successful command. | Restored targets match the saved records, with eliminated units omitted. Plans still use surviving targets, and replay returns the existing receipt without resampling, changing the snapshot, or applying arrivals twice. |
| AC-009 — Reinforcement into a zero quota | Start with `3/0/0` for objectives at rows `0`, `4`, and `8`. A later group with one unit successfully enters at row `8`. | The arrival targets row `8` by the unchanged count/distance rule. The three starting targets stay at row `0`. If deployment was blocked first, the assignment is added only on success. |
| AC-010 — Baseline and legacy | Five units start at rows `0`, `5`, `5`, `10`, `10` with objectives at `0`, `5`, `10`. Use default or explicit deterministic mode; separately force `2/2/1` in randomized mode at `p = 1`. Load a legacy save with those restored positions and no assignment field. | The deterministic runs and legacy load use `1/2/2`, cost zero, without drawing. The randomized run honors `2/2/1` despite its higher cost. A legacy read does not write; its next successful command persists the targets. |

## 6. Test automation strategy

- **Verify the law, not observed frequencies.** Drive the production sampler
  with a controlled bounded-integer source. At `p = 1/2`, force each of the
  two family tickets, then exhaust all ranks within each family. Independently
  enumerate valid vectors on small fixtures and compare the rank-to-vector
  mapping in order: every expected vector appears exactly once in the right
  family, with no duplicates, gaps, or invalid quotas. For Crossroads, this
  proves the singleton mass is `1/2` and each of the 27 other ranks has mass
  `1/2 × 1/27 = 1/54`. Also test a non-default interior probability (e.g.
  `3/4`, tickets `2` and `3` straddle the threshold), forced families, and
  singleton and no-draw cases. Do not assert approximate frequencies across
  random games, require different seeds to produce different vectors, or
  hunt for seeds that happen to exercise the all-in cases.
- **Verify optimization separately.** Use small `pytest` fixtures and an
  exhaustive reference over maps that satisfy the given quotas. Compare the
  full target sequence as well as distance and exact target counts, and keep
  the existing deterministic balance tests.
- **Verify the real lifecycle.** Exercise game creation, command commits and
  receipt replay, and codec round trips. Use a sampler that fails if called
  on restore or replay. Check the shared random state and use guarded combat
  and defensive-fire sources to detect accidental draws during initialization.
  Retain existing invalid-save, reinforcement, movement legality, and CPU
  phase-flow regressions. Run `./server-side-checks.sh` when implementing; no
  browser or PPO training run is required.

## 7. Rationale and context

Choosing quotas first varies the opening without changing the policy into
independent random movement. The default mixture keeps balanced openings
common without excluding uncommon splits. Exact distance minimization makes
each split purposeful, and fixed targets keep that choice meaningful when a
unit is blocked, displaced, or lost.

## 8. Dependencies and external integrations

Use the existing core board and player lifecycle, the scripted assignment
solver, Python's standard-library randomness, and the authoritative game-state
codec and command service. No new dependency, storage migration, or external
service is required.

## 9. Examples and edge cases

- In Crossroads, `6/0/0`, `0/6/0`, and `0/0/6` point to `(2, 3)`, `(3, 15)`,
  and `(6, 9)`, respectively. They are legal assignments, not promises that
  six units can enter or that the target will be captured.
- With fewer units than objectives, a balanced split itself has zero entries.
  For two units across three objectives, the balanced family is `0/1/1`,
  `1/0/1`, `1/1/0`; the unbalanced family is `0/0/2`, `0/2/0`, `2/0/0`.

## 10. Validation criteria

The increment is complete when AC-001 through AC-010 and the deterministic
distribution tests pass, along with existing scripted movement, reinforcement,
and persistence regressions, without changing public contracts.

## 11. Related specifications and code

- [03 - Balanced objective assignment](03-balanced-objective-assignment.md)
- [Scripted policy](../../battle_agent_rl/src/battle_agent_rl/scripted/scripted.py)
  and [balanced solver](../../battle_agent_rl/src/battle_agent_rl/scripted/balanced_assignment.py)
- [Game factory](../../battle_hexes_api/src/battle_hexes_api/gamecreator.py)
  and [core game lifecycle](../../battle_hexes_core/src/battle_hexes_core/game/game.py)
- [Game-state codec](../../battle_hexes_api/src/battle_hexes_api/persistence/game_state_codec.py),
  [hydration](../../battle_hexes_api/src/battle_hexes_api/persistence/game_state_hydrator.py),
  and [command service](../../battle_hexes_api/src/battle_hexes_api/persistence/command_service.py)
- [Crossroads on D-Day scenario](../../battle_hexes_core/src/battle_hexes_core/scenarios/d_day_crossroads.json)

## Open Questions

No questions.
