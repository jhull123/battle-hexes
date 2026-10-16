---
title: "PPO Agent 06: Multi-Unit Decision Design and Prototype"
date_created: 2026-10-14
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Use **policy-selected `(unit, destination)` decisions with immediate core movement resolution and one combat phase per side's complete turn**. The policy sees both armies and chooses which pending unit moves next as well as where it moves. This preserves the tactical choice of drawing defensive fire with one unit before moving another. Prove this contract on a fixed 9×9, two-unit-per-side prototype with interior starting positions before expanding training. Persistent unit slots, explicit pending-order inputs, and padded per-unit observations keep policy shapes stable through casualties and smaller rosters.

This is a proposed increment, not completion evidence. Increment 06 remains uncompleted until its prototype and acceptance evidence have been delivered and reviewed.

## 1. Purpose & Scope

This specification is for implementers and reviewers of increment 06 of the [implementation schedule](implementation-schedule.md). Deliver a separate local multi-unit environment, a thin Gymnasium adapter, shared state/action conversion, a bounded audited random/hold rollout command, and focused tests under `battle_agent_rl.ppo` and `battle_agent_rl/tests/ppo`. The main fixture is 2v2; 1v1, 1v2, and 2v1 are capacity/padding checks using subsets of that fixture, not a scenario curriculum.

The prototype establishes legal decisions, policy control of movement order, complete turns, stable inputs, and compatibility with masked policy prediction. It does not require optimizer updates, checkpoint selection, comparative training, or a multi-unit core `PPOPlayer`. Broader scenario training, variable boards, heterogeneous units, reinforcements, self-play, reward shaping, API/UI integration, and playing-strength claims require later specifications. Learning effective movement order is a later training outcome; the action contract supports that choice now.

## 2. Definitions

- **PPO:** Proximal Policy Optimization; the existing integration uses SB3-Contrib `MaskablePPO`.
- **Slot:** An episode-persistent position in a fixed-capacity unit roster, independent of current coordinates and board iteration order.
- **Unit decision:** One joint choice of a living pending learner unit and its destination. One environment `step` consumes one such choice; unit selection is not a separate timestep.
- **Pending unit:** A living unit that has not yet received its one destination order in this side's current turn.
- **Complete side turn:** Every surviving pending unit has received an order, including explicit holds, followed by core combat and status evaluation, unless core completion ends play earlier.
- **Cycle:** A learner side turn and, if core remains active, the opponent's complete side turn. A cycle is distinct from a unit decision and from `Game.turn_number`.
- **Hold:** The selected unit's current cell, converted to a one-hex path; it consumes that unit's decision without consuming movement points artificially.
- **Cutoff:** The configured cycle budget is exhausted while core remains `in_progress`; reported as truncation, never a core draw.

## 3. Requirements, Constraints & Guidelines

- **REQ-001:** Build the bounded scenario and persistent roster in section 4. Reject unsupported capacity, board, units, or rules before exposing a decision; never silently drop units or resize spaces.
- **REQ-002:** Let the policy choose any living pending learner slot and its destination in one action. Each unit receives at most one destination order per side turn. Apply that order immediately through core, then rebuild state and masks for all remaining pending units before the next choice. Hold completes an order even if movement points remain. Dead and padding slots require no action. Neither slot numbering nor board iteration order dictates learner movement order.
- **REQ-003:** Finish all movement choices before resolving that side's combat. Finish the opponent's entire turn before returning the next learner-turn decision. Follow the state machine in section 4, checking authoritative completion after movement, combat, and handoff. A non-ending return always exposes a learner decision with at least hold legal.
- **REQ-004:** Encode the exact fixed observation and action spaces in section 4. Include pending orders for both learner slots, current positions and movement, and defensive-fire state. Inputs must reflect actual resolved core state, including stacked units, retreats, removals, and fire already spent earlier in the same turn. There is no preselected acting unit in the observation.
- **REQ-005:** Derive legal destinations and paths from current core reachability/pathfinding for the selected unit. Reject invalid actions before changing core state, pending state, counters, events, or RNG state. Never silently replace a rejected action with hold.
- **REQ-006:** Reward only authoritative episode outcomes: learner win `+1`, loss `-1`, draw or any nonterminal transition `0`. Budget complete cycles rather than unit decisions, so losing a unit does not grant extra turns. Report decisions and cycles separately; use section 4's completion-over-cutoff precedence.
- **REQ-007:** Use a live-state opponent that samples uniformly from legal `(unit, destination)` actions using the seeded game RNG. Provide random and hold learner policies and deterministic replay of structured traces, with the seed protocol in section 4. Opponent choices must also use freshly recomputed legal masks after preceding moves.
- **REQ-008:** Expose a Gymnasium `Dict` observation, `Discrete(162)` action, and native `action_masks()` for the new contract. Demonstrate mask-aware predictions from a freshly initialized `MaskablePPO` `MultiInputPolicy`, without training. Audit random/hold traces against core and record bounded prototype evidence.
- **CON-001:** Keep core authoritative for movement, fire, retreat, combat grouping, and victory. Add no PPO dependencies or policy methods to core. Scheduling one order per unit is the prototype's action restriction, not a change to core movement rules.
- **CON-002:** Keep the 01–05 environment, artifact identifier, evaluation protocol, and `PPOPlayer` supported as their existing fixed 1v1 task. The new contract is incompatible even when the multi-unit prototype runs with one unit per side. Do not reinterpret an existing checkpoint as a multi-unit policy.
- **CON-003:** Separate roster/state encoding, selected-unit action conversion, side-turn orchestration, Gym adaptation, and trace presentation into cohesive components. Share suitable core-resolution helpers rather than duplicating entire turn workflows. Resolve proposed deviations from numbered specifications with the user before implementation.

## 4. Interfaces & Data Contracts

### 4.1 Supported scenario and roster

Contract identifier: `battle-hexes-9x9-2slot-unit-destination-live-v1`.

Use two CPU sides, learner first, one faction each, on `Board(9, 9)`. All units are infantry with attack/defense/move `2/2/2`, defensive-fire modifier `1.0`, and normal initial readiness. Use defensive-fire base probability `0.25` with the existing default clamps, no terrain, roads, objectives, reinforcements, or core turn limit. Keep core's default `stacking_limit=None`: friendly stacking is legal and must be represented without losing a unit.

| Side | Slot within side | Unit ID | Initial position |
| --- | --- | --- | --- |
| Learner | 0 | `learner-0` | `(3, 2)` |
| Learner | 1 | `learner-1` | `(5, 2)` |
| Opponent | 0 | `opponent-0` | `(3, 6)` |
| Opponent | 1 | `opponent-1` | `(5, 6)` |

These interior starts preserve the four-column separation of the earlier proposed 5×5 multi-unit fixture while adding room around the initial engagement for two-hex combat retreats. They do not guarantee every retreat succeeds: direction, other units, and later movement still matter under core rules. Keep both interior successful-retreat and edge-blocked-retreat fixtures in acceptance coverage.

The default is 2v2. Each side may instead start with only its slot-0 unit for the three smaller-roster checks. Require one or two initial units per side; zero initial units and more than two are unsupported. Zero living units during play is handled through core completion.

Capture the slot-to-unit mapping at reset, with global observation slot order `[learner-0, learner-1, opponent-0, opponent-1]`. Never compact or reuse slots after death. Missing initial slot 1 remains padding throughout the episode. Distinguish missing and eliminated units using `present` and `alive`. Do not derive identity from coordinates, list position in `get_units_for_player`, or `get_unit_at`, which returns only one occupant of a stack. Validate unique IDs and insert the fixture's units in this canonical order so core tie-breaking/iteration is reproducible too. Fresh resets recreate all mutable state.

### 4.2 Action, mask, and order completion

Action `a` in `Discrete(162)` jointly selects a learner slot and a row-major destination:

```text
slot = a // 81                  # side-local slot 0 or 1
cell = a % 81
destination = (cell // 9, cell % 9)
a = slot * 81 + row * 9 + column
```

Indexes `0..80` belong to learner slot 0 and `81..161` to learner slot 1. Both blocks may contain legal actions at the start of a turn. The policy emits one categorical choice over this joint space, not independent unit and destination choices whose masks could disagree. The opponent uses the same encoding relative to its own two slots. Enemy units are never selectable by a learner action.

At an active decision:

1. Build a two-row, 81-destination mask for the current side. An absent, dead, or already-ordered slot has an entirely false row.
2. For each living pending unit, obtain its current hex and core reachable hexes with `move_points=unit.current_turn_movement_points_remaining` explicitly. Mark exactly those destinations as legal in its row, including its current cell. Flatten in slot-major order to match `a = slot * 81 + cell`.
3. Validate a scalar integer action (including scalar NumPy integers, excluding booleans, floats and non-scalar arrays), bounds, and the current mask before mutation. Decode its slot and destination; require that unit to be living, pending, and owned by the current side.
4. Obtain `board.shortest_path(unit, start, destination)` and require a nonempty route with correct endpoints within the current movement budget. Hold is `[start]`. A missing/inconsistent route is an error, not a fallback.
5. Apply exactly that `UnitMovementPlan` using `game.apply_movement_plans([plan])`; mark the unit's order consumed even if fire interrupts movement, forces retreat, or eliminates it. Do not grant a second order for unused movement points or failure to reach the intended destination.

`shortest_path` currently uses the unit's full move allowance. In this prototype every selected unit is receiving its first order of the turn and has the full allowance; assert that invariant before mutation. Reachability still receives the remaining allowance explicitly. Supporting split orders or a partially spent unit awaiting its first order would need a separately reviewed path-budget contract, not reliance on that default.

There is no separate unit-selection step or end-turn action. A unit with only hold legal still receives one explicit hold decision, before or after another unit as the policy chooses. A completed order masks out that unit's entire action block, and exhausting pending units closes movement automatically. Thus a nonterminal side turn requires at most two choices and cannot stall through repeated holds. Dead and padding blocks remain in the fixed action space but are entirely masked out.

The mask is a fresh `bool[162]`; all entries are false after termination or truncation. Do not request a policy prediction on an ending. A non-ending all-false mask is an invariant failure, not an implicit end-turn command.

### 4.3 Turn state machine

At reset, initialize learner pending bits from living learner slots. The first returned state permits either pending unit to move first; no actor is selected until an action is submitted.

Each learner `step(action)` performs:

1. Validate and apply the selected unit order as above; increment `decision_count`. Core movement includes defensive fire and its own status update. Read status immediately; if completed, return the terminal state without additional movement, combat, or handoff.
2. If a living learner pending slot remains, return a zero-reward intermediate transition with freshly computed action blocks for all remaining pending slots. **Do not resolve combat, call `next_player`, refresh movement budgets manually, or move the opponent here.** Earlier units' positions and fire effects are already visible.
3. Otherwise resolve learner combat once with `Combat(game, rng=game_rng).resolve_combat()`, then `game.update_game_status(finalize=True)`. Read status; stop if completed.
4. Advance with `game.next_player()`, check status, and initialize opponent pending bits from its living slots. Sample each joint `(unit, destination)` action uniformly from its sorted current legal indexes, apply it immediately, and check status after each order. Resolve opponent combat once only after its pending units are exhausted and only while active; refresh/read core status.
5. If active, advance back with `game.next_player()` and check status. Count the cycle as completed when both side turns have finished, including if opponent combat or the final handoff completes the game. If still active and the cycle budget is exhausted, return a cutoff. Otherwise reset learner pending bits from living slots and return the next learner decision.

On completion before both turns finish, leave the cycle uncompleted and record the phase of completion; an episode may end after its first unit decision. Remove any eliminated unit from pending selection. In the supported elimination scenario, no living learner while core still reports an active decision is an invariant failure; ask core to evaluate status rather than synthesizing a loss from unit counts.

`apply_movement_plans` invokes `movement_cb()` per call and updates readiness/status. Prototype players use no-op callbacks; neither callback counts turns nor finalizes rewards. Do not call existing `turn_resolution.play_turn` or `play_cycle` once per unit: those helpers resolve combat and handoff too early for this contract. Factor/share an appropriate combat/status boundary if reusing the 1v1 code, with regression coverage for 01–05.

The default `cycle_limit` is 50, a positive integer fixed for an environment instance. `completed_cycles` begins at zero; `remaining_cycles = cycle_limit - completed_cycles` stays constant between unit choices of the same cycle. A final allowed cycle must finish all still-applicable learner and opponent actions and combat before truncation. Completion at any point takes precedence: `terminated=True`, `truncated=False`. A cutoff has `terminated=False`, `truncated=True`, reward `0`, and core status `in_progress`. Further steps fail until reset. There are at most `2 * cycle_limit` learner decisions per episode.

### 4.4 Observation space

Use a Gymnasium `Dict` with the following fields. All arrays are fresh copies. Binary fields are `MultiBinary` with `int8` values; there is no implicit scalar unit-ID encoding or floating-point normalization. The policy receives the complete four-slot state, not a selected-unit crop.

| Field | Space / shape | Meaning |
| --- | --- | --- |
| `positions` | `MultiBinary((4, 81))` | One row-major position bit per living slot; zero row for dead/padding. Friendly stacked units have independent bits in the same column. |
| `present` | `MultiBinary(4)` | Slot was populated at reset; stays 1 after elimination. |
| `alive` | `MultiBinary(4)` | Unit currently exists on the core board. |
| `movement_remaining` | `Box(0, 2, (4,), int8)` | Current core movement points, not number of orders left. |
| `defensive_fire_ready` | `MultiBinary(4)` | `unit.public_defensive_fire_status(learner)` for each living unit. |
| `fire_eligible_last_turn` | `MultiBinary(4)` | Core `ended_last_friendly_turn_with_defensive_fire_eligibility`. |
| `forced_retreat` | `MultiBinary(4)` | Core `forced_to_retreat_since_last_friendly_turn`. |
| `fire_spent` | `MultiBinary(4)` | Core `defensive_fire_spent_this_off_turn`. |
| `pending` | `MultiBinary(2)` | Living learner slots still awaiting an order in this turn; the policy may choose any set slot through its action block. |
| `remaining_cycles` | `Box(0, cycle_limit, (1,), int32)` | Remaining complete-cycle budget, including the current cycle. |

This is **355 scalar inputs**: 324 position bits, 28 per-slot state values, two pending-order bits, and one budget value, plus a separate 162-bit legal mask. No shape changes as units die or for the supported smaller initial rosters. At every active decision at least one `pending` bit is set; each set bit identifies a living unit with at least its hold action legal. For dead/padding slots, zero all per-unit fields except dead slots retain `present=1`. At either ending, clear `pending`, retain the actual final living-unit state, and return an all-false action mask. An early completion may retain positive `remaining_cycles`; a cutoff has zero.

The explicit readiness and underlying history bits are deliberately slightly redundant: multi-unit decisions now occur inside movement, where movement spent and fire spent earlier in the same turn matter. Encoding them avoids depending on the 1v1 assumption that all observations occur after a fresh turn reset. Their values come from core; the encoder does not recalculate readiness rules.

Audit coverage:

| Decision factor | Contract treatment |
| --- | --- |
| Identity, positions, stacks, losses, smaller rosters | Persistent slots, `positions`, `present`, `alive`. |
| Which units may act and which have finished | `pending`, independent of remaining movement points; the action chooses the next unit. |
| Movement/path legality | Current core-derived mask and validated path; `movement_remaining` exposes mutable budget. |
| Current and next-turn defensive-fire consequences | Readiness, remaining movement, prior eligibility, retreat and spent flags. |
| Attack/defense/type, terrain, geometry, fire settings | Fixed scenario constants; actual movement and adjacency remain core-owned hex rules. |
| Finite horizon | `remaining_cycles`; pending bits distinguish partial turns within that horizon. |
| Turn number, IDs, status, chosen path, event history | Diagnostic only; no additional outcome-relevant turn rule exists in this fixture. |
| Future opponent choices, future rolls, RNG state | Private stochastic state, never observation features. |

Document any reachable pair of states with identical policy inputs but different relevant mutable state found during the audit. Resolve such a gap before accepting the prototype, rather than claiming general observation sufficiency from the table alone.

### 4.5 Environment, randomness, diagnostics, and policy boundary

Provide a separate environment with `reset(seed)` and `step(action)` returning the existing structural `Transition` fields: `observation`, `legal_action_mask`, `reward`, `terminated`, `truncated`, `info`. A thin Gym adapter returns standard reset/step tuples and implements `action_masks()`. Require `observation_space.contains` at reset, intermediate decisions, next-turn decisions and endings. Keep the lightweight environment/random inspector usable without trainer dependencies.

One `random.Random(game_seed)` drives opponent selection and all core combat/fire randomness. Sample uniformly from the sorted legal joint-action indexes, using one choice per order. This weights a pending unit in proportion to its number of legal destinations; it is deliberately not uniform-unit-then-uniform-destination sampling. Do not reuse `SeededRandomPlayer.movement()` unchanged: it constructs the whole list on the pre-movement board. The prototype opponent uses the same selected-unit conversion and complete-turn scheduler as the learner, with random selection internal to the driver. Learner random policy uses its own `random.Random(game_seed)` and the same uniform joint-action sampling. Learner hold selects the lowest-numbered pending slot and encodes its current cell with the slot offset; this deterministic ordering defines only the hold baseline, not a restriction on PPO or random play. Gym explicit `reset(seed=s)` restarts at seed `s`; automatic resets advance to `s+1`, `s+2`, etc., and seed the action space as in 03. Repeated seeds mean repeated trajectories only with matching actions, fixture, ordering, and RNG consumption.

Required `info` fields include contract identifier, episode seed, slot-to-ID mapping, core status/turn number, `decision_count`, `completed_cycles`, submitted action index and decoded selected slot, intended destination/path, whether this step closed the learner turn/cycle, and movement/fire/combat records attributed to side and phase. Reset has no submitted action, selected slot, or destination. End summaries report `win`, `loss`, `draw`, or `cutoff`, learner decision length, completed cycles, and episode return. Snapshot event values when captured; do not use a mutable unit's final position as its historical event position. `info` is not a policy input.

Suggested local invocation (proposed, not an existing command):

```sh
PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src python -m battle_agent_rl.ppo.multi_unit.inspect --seed 0 --cycle-limit 10 --policy random
PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src python -m battle_agent_rl.ppo.multi_unit.inspect --seed 42 --cycle-limit 1 --policy hold --expect-ending cutoff
```

Document the final module path consistently. Print labeled unit slots/stack contents, pre-action inputs/mask, selected unit/destination, resolved events, phase/cycle progress, and final outcome. Audit against live core state at each return, exit nonzero on inconsistencies or an unexpected ending, and use structured assertions rather than exact transcript snapshots.

Prediction is `model.predict(obs, action_masks=env.action_masks(), deterministic=True)` with a model constructed for these new spaces. The initialized-model smoke check proves shape and masking compatibility only. Old 1v1 artifacts must fail a contract/space compatibility check before prediction; both the action space and observation contract differ. Durable multi-unit artifacts and a new training command are not required here.

The existing core `Player.movement() -> list[UnitMovementPlan]` is a whole-turn pre-resolution callback. It cannot obtain the observed result of the first unit's defensive fire before returning the second unit's plan. Therefore this prototype uses an explicit local environment driver with core-compatible plans, **not** a claimed drop-in multi-unit `PPOPlayer`. Do not simulate future rolls to construct a batch, mutate the real game from `movement()`, or silently move combat earlier. A later inference increment must design an incremental decision boundary or choose a separately specified batch-planning policy; training/inference conversion must then agree on that boundary.

### 4.6 Credit assignment

All unit decisions belong to one learner episode and one team objective. Each joint action's log-probability covers both unit selection and destination, allowing eventual PPO updates to assign credit to movement order without a separate selector policy or reward. Intermediate decisions, unit deaths, and completed turns do not reset episode state or produce unit-specific rewards. Emit the terminal team reward exactly once, on the transition that actually observes core completion, including when it includes the opponent turn. Earlier unit choices receive credit through returns across subsequent unit decisions; do not copy the final reward onto each unit or infer damage rewards.

For later use of this contract, one PPO timestep means one unit decision. Ordinary per-step discounting would discount outcomes more heavily while two learner units survive than while only one survives. The prototype's return is the undiscounted sum of rewards; an initial future trainer adopting this contract must use `gamma=1` to preserve that episodic objective, or separately specify and justify a cycle-aware discount scheme. Advantage estimation and optimization experiments are later work. This choice avoids a hidden timing bias but does not solve sparse joint credit assignment or demonstrate learned coordination.

## 5. Acceptance Criteria

- **AC-001 — Complete turns:** Given two living learner units, either slot may act first. After its move or hold, the returned state masks out its entire block, leaves the other pending slot's legal actions available, retains the same current player/cycle budget, and contains no combat or opponent movement. After the other slot orders, resolve learner combat once and the complete opponent turn before the next learner decision, unless authoritative completion intervenes. Verify both slot orders, including slot 1 before slot 0.
- **AC-002 — Current legality:** Given an active decision, every true mask entry decodes to a living pending unit and a valid current core path for it, including hold. Dead, padding and already-ordered slots have all-false blocks. Invalid types/indexes/masked actions and route failures leave board, unit state, pending bits, counts, events, and RNG unchanged. A move/hold consumes one order; remaining movement cannot grant another.
- **AC-003 — Live fire effects:** Given controlled movement that spends an opponent's defensive fire and retreats or removes the first mover, the next learner decision reflects its actual position/death and the opponent's spent/readiness state. That mover's entire action block is masked out, regardless of its slot number. Combat has not occurred between those choices.
- **AC-004 — Stable identity and shapes:** Given 2v2, 1v1, 1v2, 2v1, a dead slot 0 with slot 1 surviving, and a friendly stack, observations remain within the same declared spaces and masks remain length 162. The survivor retains its slot and action block; stack rows both retain positions and have distinct hold indexes; dead and padding fields follow the specified zeroing/presence rules. More than two units, duplicate IDs, and unsupported settings fail rather than truncating inputs.
- **AC-005 — Joint combat:** Given both learner units moved into a connected engagement, combat after the final order uses the core-discovered multi-unit group. Tests also cover hold-only turns with an existing engagement: holds do not suppress combat. Use observable participants/results rather than asserting a private helper call.
- **AC-006 — Endings and budget:** Given `cycle_limit=1` and the fixed distant-start hold learner, finish both learner choices and all applicable opponent actions before reporting an active-game cutoff. Cover core win, loss and draw, completion during movement, and completion in either side's final-cycle combat. Completion takes precedence over cutoff; dead units require no dummy steps; all ending masks are false and further steps fail until reset.
- **AC-007 — Bounded replay:** Given the same fixture, seed, policy, and cycle limit, two traces agree on actions, observations, masks, events and endings. Random and hold learner sweeps over seeds `0..19` with limit 10 have no illegal decisions, empty active masks, or episodes exceeding 20 learner decisions. Repeated reset creates fresh state and reproduces the original seed; automatic resets advance seeds.
- **AC-008 — Policy compatibility:** Given a freshly initialized CPU `MaskablePPO` with these spaces, masked prediction works when both slot blocks are available, when only slot 0 or only slot 1 is pending, and on reduced-roster and post-casualty states, including a hold-only mask. Every prediction decodes to a legal unit/destination and weights remain unchanged. A 01–05 policy/artifact fails compatibility validation before prediction.
- **AC-009 — Audit and regressions:** Given the documented command and targeted fixtures, the inspector verifies observations, scheduling, legal paths and outcomes against core and fails on a deliberately inconsistent input. The full server-side checks continue to pass, including the existing 1v1 inspection, evaluation, and inference contracts.
- **AC-010 — Defensive-fire order choice:** Given a controlled position where either learner unit can enter adjacency to the same ready defender, replay from identical initial state/RNG with slot order `0,1` and `1,0`. Use a no-effect fire roll so both intended moves remain possible. The defender fires at the first selected mover, is visibly spent before the second decision, and does not fire again at the second mover in that turn. Verify both orderings are legal and that changing order changes the recorded fire target. This proves tactical control of exposure, not that an initialized policy chooses an advantageous order.
- **AC-011 — Interior and edge retreats:** Given controlled 9×9 combat positions and a forced two-hex retreat result, an unobstructed interior retreat completes both hexes and retains the unit. In a corresponding edge case where the retreat would leave the board, core eliminates the unit under its existing failed-retreat rule. Verify final positions/alive bits and core combat events in both cases, retaining another same-side unit where needed to inspect a subsequent decision. The default reset must use the specified interior starts; do not move them to the edges to make completion easier.

## 6. Test Automation Strategy

Use focused `pytest` tests under `battle_agent_rl/tests/ppo` and real core transitions. Construct small controlled positions on the fixed 9×9 board and deterministic game RNG/roll fixtures for defensive-fire retreat/elimination, successful interior two-hex combat retreats, edge-blocked combat retreats, spent fire, reversed unit-order exposure, stacks, grouped combat, and terminal outcomes; do not search unbounded random seeds for coverage. Clone/reset fixtures when checking every legal joint action so one trial cannot change another's starting state. Check slot-offset encoding/decoding and all-false unavailable blocks explicitly. Verify core status and public events, board state, and unit state rather than exact logs or private call sequences.

Check no-mutation failures including RNG progression. Exercise the Gym adapter on partial turns, full-cycle returns, endings and resets. Do not use an unmasked generic environment checker that can sample illegal destinations. Keep the initialized-model compatibility check bounded, use the existing optional trainer dependencies, and perform no optimizer update. Confirm repeated frozen predictions do not change weights.

Run the 40 bounded random/hold episodes in AC-007 and record separate win/loss/draw/cutoff counts, decisions, and cycles as plumbing evidence. Run `./server-side-checks.sh` after implementing the prototype. No browser tests, training convergence gate, win-rate target, benchmark, or held-out skill experiment is required for 06.

## 7. Rationale & Context

### Contract comparison

Let `B=81` cells and capacity `U=2` units per side. All credible designs need global board/unit state to account for friendly blocking/stacking, joint combat, and defensive fire; cropping to the acting unit alone is insufficient.

| Scheme | Turn timing | Legal masking | Variable unit counts | Credit assignment | Input/output size and cost |
| --- | --- | --- | --- | --- | --- |
| **Chosen: live `(unit, destination)` decisions, automatic turn completion** | Policy chooses move order; apply movement/fire immediately; combat once after all orders; opponent only after learner turn. | Exact current-state `U*B=162`-bit mask; each slot block uses that unit's legality and pending status. Later choices see resolved fire. | Pad roster/action blocks to capacity; mask dead/finished slots; automatically close turn after pending units. | Up to `U` transitions per turn with sparse shared reward; joint action credit includes order and destination. Explicit discount convention required. | Fixed global input plus pending bits; 162 logits per choice, at most two choices per side. |
| Fixed-order, live per-unit destinations | Same movement/fire/combat boundaries, but a scheduler forces unit order. | Exact `B=81`-bit mask for the preselected unit. | Persistent padded slots; skip dead units; automatic completion. | Sparse per-decision team credit, but the policy cannot assign credit to an order choice it never makes. | Global input plus actor/pending bits; 81 logits. Smaller head, but excludes choosing who draws defensive fire. |
| Whole-turn destination orders | One policy decision can match `Player.movement()` and then resolve ordered plans/combat. All choices precede fire. | A joint categorical needs up to `B^U=6561` combinations even here. Independent `MultiDiscrete([81,81])` masks cannot express interdependent destinations/paths or changes caused by earlier fire. Must specify conditional legality, reservation, and interrupted/stale orders. | Pad dead slots with a compulsory no-op and include alive mask; joint space grows exponentially with capacity. | One team reward transition per cycle simplifies temporal bookkeeping but attributes outcomes to a whole order vector. | Similar global input without pending cursor; 6561 categorical logits, or 162 factorized logits with an insufficient independent-mask contract. |
| Policy-selected `(unit, destination)` plus end-turn | Same live order choice, but policy explicitly ends movement. | Flat mask of `U*B+1=163`; mask dead/finished units and define whether omitted orders become holds. | Persistent slots and pending bits still necessary; bounds needed to prevent repeated orders/stalling. | Also sparse per-decision team credit, plus learning when to finish. | Similar global input; 163 logits and an unnecessary stop decision for a two-unit, explicit-hold prototype. |
| Autoregressive whole-turn planning | Choose destinations conditioned on an order prefix, then submit a batch. If actual movement/fire runs between choices, this becomes live sequential control instead. | Prefix reservations can handle deterministic conflicts, but cannot know later legal state after unresolved stochastic fire without a specified contingent-order model. | Padded slots or a variable decoder; termination token needs rules. | Can train joint log-probability for one turn or separate prefix transitions; requires an explicit custom learning interface. | Global state plus prefix context; `O(U*B)` output work, with decoder/distribution machinery beyond the existing simple masked policy. |

Choose joint unit/destination actions because defensive fire makes movement order part of the tactical decision. Core spends a defender's fire even on a no-effect shot; choosing which unit draws that shot can change another unit's exposure. Fixed order would exclude this choice before training starts. At two units on 9×9, expanding from 81 to 162 logits is a small cost and still uses the existing ordinary masked categorical policy; no separate selector network or autoregressive decoder is required. Immediate core resolution lets later choices react to actual fire/retreat results, while automatic completion after explicit orders/holds guarantees finite complete turns without a stop token. This gives the future trainer control of order without claiming it will learn a good order.

### Board size and edge bias

A 5×5 board puts much of play close to an edge, where an otherwise ordinary two-hex combat retreat can become elimination. That can overemphasize center occupation and edge avoidance relative to larger games. Choose fixed 9×9 with interior starts to give the initial engagement more retreat space while keeping the two-unit prototype bounded. Edge rules remain valid and explicitly tested; increasing board size is not a change to combat or retreat rules and does not guarantee that later play avoids edges.

A larger board reduces this structural edge pressure but one fixed starting layout can still encourage layout-specific behavior. Varied starting positions and broader scenarios belong in a later training increment with its own evaluation protocol. The 06 fixture and controlled edge/interior tests prove the contract, not generalization or a learned reduction in edge bias.

### Observation choice and scale limit

The 1v1 occupancy/readiness planes use `get_unit_at` and cannot distinguish two friendly occupants, their readiness, or which unit has already acted. Fixed per-unit position planes preserve all four identities and stacks, while pending-order bits distinguish equal boards at different points within a turn. Flattening 355 inputs is small enough for the existing `MultiInputPolicy`; no graph network or attention mechanism is necessary to prove the boundary. An acting-unit input is unnecessary because the joint action selects it from the globally observed pending units.

This representation scales as `O(U*B)` for both sides and is neither permutation-invariant nor a solution to arbitrary boards/armies. A compact padded entity table with coordinates would reduce position inputs to `O(U)` but require learning coordinate relationships; a board-count representation alone would lose individual state and selection identity. Entity/attention or graph representations are credible later alternatives when board/capacity growth justifies them. For 06, changing board dimensions or capacity is a new incompatible contract, not runtime resizing or clipping.

The completed 04 comparison did not support improvement over all baselines, and 05 proved only 1v1 inference integration. Neither result supplies evidence of multi-unit skill. This increment tests whether multi-unit trajectories are well-defined and observable, not whether adding units improves training.

## 8. Dependencies & External Integrations

- **DAT-001:** Lessons from 01–05: current-state encoding, core-derived masks, explicit cutoff inputs, seeded transitions, contract validation, and inspection independent of training.
- **EXT-001:** Core `Game.apply_movement_plans`, `Game.next_player`, `Game.update_game_status`, `Combat`, `Board.get_reachable_hexes`/`shortest_path`, `UnitMovementPlan`, unit defensive-fire state, and known/living unit accessors.
- **PLT-001:** Existing supported Python environment and lightweight test stack; existing Gymnasium/NumPy/SB3-Contrib CPU dependencies for the adapter and initialized-policy check. No new service or training framework.
- No HTTP API, frontend, deployment, external scenario corpus, or network integration is required.

## 9. Examples & Edge Cases

- At reset, learner `pending=[1,1]` and `remaining_cycles=[50]`. Hold for slot 0 at `(3,2)` is action `3 * 9 + 2 = 29`; hold for slot 1 at `(5,2)` is action `81 + 5 * 9 + 2 = 128`. Either can be selected first. Selecting `128` leaves `pending=[1,0]`, masks out indexes `81..161`, retains slot 1's movement points at `2`, and leaves the cycle budget unchanged. Then action `29` closes learner movement and triggers the rest of the cycle.
- If slot 1 moves first and is eliminated by defensive fire, its `present` stays 1, `alive` becomes 0, and its position/state rows are zero. Slot 0 may act next if core is still active. Eliminating one unit does not end a multi-unit episode automatically.
- If slot 0 dies in combat and slot 1 survives into the next learner turn, `pending=[0,1]`; only indexes `81..161` can be legal and one order now closes learner movement. This cycle still consumes one cycle of budget.
- If both friendly units occupy center cell 40 at `(4,4)`, both position rows contain a 1 at column 40. Action `40` holds slot 0; action `121` holds slot 1. If both are pending, both holds are legal. A single occupancy sign cannot encode this case.
- The policy may send slot 1 first to draw a defender's fire, then choose slot 0's destination using the defender's changed readiness. Reversing order may expose slot 0 instead. The second decision sees actual fire/retreat effects even if the first unit's intended destination was not reached; the contract promises neither a successful bait nor a learned tactic.
- A completed loss during the first learner move stops immediately; do not manufacture orders for the remaining roster or run opponent combat after core completion. A nonterminal hold-only final cycle still includes opponent activity before cutoff.

## 10. Validation Criteria

Deliver the separate prototype, documented commands and schema, completed observation audit, and acceptance tests AC-001 through AC-011. Record audited two-choice learner turns in both slot orders, reversed-order defensive-fire target evidence, a subsequent single-survivor turn, a fire-interrupted move followed by another decision, successful interior and edge-blocked two-hex combat retreats, a stack, a completed episode, and a full-cycle cutoff. Include the bounded seed-sweep counts and initialized-model mask compatibility result, with runtime versions and seed settings. Evidence may use controlled fixtures for specific events; distinguish those from untouched random rollouts.

Passing checks establishes the legality, timing, and shape contract only. Writing this specification does not mark 06 done. After the prototype is implemented and its evidence verified, follow the schedule's completion process to update the schedule and `battle_agent_rl/PPO.md`; broader training, self-play, API/UI integration, and any skill claim remain separately gated increments.

## 11. Related Specifications / Further Reading

- [01 — Minimal training environment](01-training-environment.md)
- [02 — Rollout inspection and observation audit](02-rollout-inspection.md)
- [03 — First masked PPO training loop](03-masked-ppo-training.md)
- [04 — Evaluation, visualization, and checkpoints](04-evaluation-and-checkpoints.md)
- [05 — Inference player in core games](05-inference-player.md)
- [Implementation schedule](implementation-schedule.md)
- [PPO agent vision and current evidence](../../battle_agent_rl/PPO.md)
- [Current PPO state conversion](../../battle_agent_rl/src/battle_agent_rl/ppo/policy_state.py), [turn resolution](../../battle_agent_rl/src/battle_agent_rl/ppo/turn_resolution.py), and [inference boundary](../../battle_agent_rl/src/battle_agent_rl/ppo/inference.py)
- [Core game operations](../../battle_hexes_core/src/battle_hexes_core/game/game.py), [movement](../../battle_hexes_core/src/battle_hexes_core/game/movement.py), and [unit readiness](../../battle_hexes_core/src/battle_hexes_core/unit/unit.py)

## Open Questions

No questions.
