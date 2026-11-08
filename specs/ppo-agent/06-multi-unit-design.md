---
title: "PPO Agent 06: Multi-Unit Decision Design and Prototype"
date_created: 2026-10-14
last_updated: 2026-10-16
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Choose **policy-selected `(unit, destination)` actions**, resolving movement and defensive fire immediately, with combat once after each side finishes its orders. The policy sees both armies and can choose which unit draws defensive fire before moving another. Increment 06 is **implemented**; see the [schedule](implementation-schedule.md) for completion evidence.

## 1. Purpose & Scope

Prove this contract in a separate fixed 9×9, two-unit-per-side prototype under `battle_agent_rl.ppo`: environment, thin Gymnasium adapter, shared state/action conversion, and bounded local random/hold inspection. Smaller rosters test padding, not a scenario curriculum.

Training, checkpoint selection, a multi-unit core `PPOPlayer`, variable boards, heterogeneous units, reinforcements, broader scenarios, self-play, API/UI integration, and skill claims belong to later increments.

## 2. Definitions

- **Slot:** An episode-persistent unit identity, independent of coordinates or board iteration order.
- **Decision:** One joint unit/destination choice; one learner `step` consumes one decision.
- **Pending:** A living unit that has not received its one order this side turn.
- **Cycle:** A learner turn followed, if core remains active, by the opponent's complete turn.
- **Hold:** The selected unit's current cell; consumes its order without artificially spending movement points.

## 3. Requirements & Constraints

- Core owns movement, defensive fire, retreat, combat grouping, and victory. PPO code schedules decisions and assembles transitions.
- Each unit receives at most one order per side turn. The policy chooses order; exhausted pending units close movement automatically. There is no end-turn action.
- Preserve the existing 01–05 environment, artifacts, and inference player. This contract is incompatible with them even when only one unit per side survives.
- Keep encoding/action conversion, turn orchestration, Gym adaptation, and inspection cohesive and separate; share suitable core-resolution helpers without copying whole workflows.

## 4. Interfaces & Data Contracts

### Scenario and persistent slots

Contract identifier: `battle-hexes-9x9-2slot-unit-destination-live-v1`.
Use `Board(9, 9)`, two CPU sides with one faction each, learner first. Infantry have attack/defense/move `2/2/2`, defensive-fire modifier `1.0`, and normal initial readiness. Fire base probability is `0.25` with existing default clamps. No terrain, roads, objectives, reinforcements, or core turn limit; `stacking_limit=None` permits friendly stacks.

| Side | Slot | Unit ID | Initial position |
| --- | --- | --- | --- |
| Learner | 0 | `learner-0` | `(3, 2)` |
| Learner | 1 | `learner-1` | `(5, 2)` |
| Opponent | 0 | `opponent-0` | `(3, 6)` |
| Opponent | 1 | `opponent-1` | `(5, 6)` |

Support 2v2 and subsets 1v1, 1v2, 2v1 by omitting each side's slot 1. Reject unsupported settings, duplicate IDs, and initial counts outside one or two per side. Reset creates fresh mutable state and inserts units in the table's order for reproducible core tie-breaking.
Observation slots always follow `[learner-0, learner-1, opponent-0, opponent-1]`. Never compact or reuse slots after death. Missing slots stay padding; eliminated units retain identity. Read all units, not `get_unit_at`, which loses stack occupants.

### Actions and masks

Use `Discrete(162)`, one categorical choice over two slot blocks of 81 row-major destinations:

```text
slot = action // 81
cell = action % 81
destination = (cell // 9, cell % 9)
action = slot * 81 + row * 9 + column
```

A fresh `bool[162]` mask marks exactly core-reachable destinations for each living pending unit, including hold. Pass its current movement points explicitly to `get_reachable_hexes`. Absent, dead, and already-ordered slots have all-false blocks. The opponent uses the same mapping relative to its own slots.
Require a scalar integer action (including NumPy integers, excluding booleans), valid bounds/mask, and a nonempty core `shortest_path` with correct endpoints and legal budget before mutation. Failures leave game, pending state, counters, events, and RNG unchanged; never substitute hold.
Core `shortest_path` currently uses full movement allowance. Assert that a selected pending unit still has its full allowance, as expected for its first order; split orders or partially spent pending units are unsupported. Hold uses `[start]`.

### Live movement and turn timing

At reset or a new learner turn, set pending bits from living learner slots. Each `step`:

1. Apply the chosen `UnitMovementPlan` through `game.apply_movement_plans([plan])`, consume its order, and increment the decision count. Fire, retreat, or elimination does not grant another order.
2. Read core status; stop immediately if completed. If learner pending units remain, return their current observation/mask with zero reward. No combat, handoff, or opponent movement occurs between learner orders.
3. Otherwise resolve learner combat once through `Combat(game, rng).resolve_combat()` and `game.update_game_status(finalize=True)`. If active, advance via `game.next_player()`.
4. Run the opponent's complete turn using the same live one-order-per-unit protocol, then its single combat resolution and status update. If active, hand back to the learner. Check core status after every movement, combat, and handoff; never continue after completion.

Callbacks are no-ops for episode bookkeeping. Do not invoke existing `play_turn`/`play_cycle` once per unit: that would resolve combat too early. Every non-ending return is a learner decision with at least one legal hold; an empty active mask is an invariant failure.

### Cutoff and reward

`cycle_limit` is a positive integer, default 50. `completed_cycles` starts at zero and increments when both side turns finish, including completion at opponent combat/final handoff; earlier terminal endings leave that cycle incomplete. `remaining_cycles = cycle_limit - completed_cycles` stays constant between choices within a cycle.
Finish all applicable movement and combat in the final allowed cycle before cutoff. Core completion takes precedence (`terminated=True`, `truncated=False`); otherwise budget exhaustion is `truncated=True` with core still `in_progress`. Reject further steps until reset. At most `2 * cycle_limit` learner decisions occur.
Emit team reward once at core completion: win `+1`, loss `-1`, draw `0`; every other transition, including cutoff, gives `0`. Unit death and turn completion do not reset the episode. Returns can credit earlier choices, but sparse joint credit assignment remains a later training problem.

### Observation

Use a Gymnasium `Dict` of fresh arrays with these exact fields. Binary spaces use `int8`; values are unnormalized. All four units are visible, with no preselected actor or future RNG/roll information.

| Field | Space | Meaning |
| --- | --- | --- |
| `positions` | `MultiBinary((4, 81))` | One row-major position bit per living slot; independent rows preserve stacks. |
| `present` | `MultiBinary(4)` | Populated at reset, including units later eliminated. |
| `alive` | `MultiBinary(4)` | Currently on the core board. |
| `movement_remaining` | `Box(0, 2, (4,), int8)` | Current movement points, not remaining orders. |
| `defensive_fire_ready` | `MultiBinary(4)` | `unit.public_defensive_fire_status(learner)`. |
| `fire_eligible_last_turn` | `MultiBinary(4)` | Core `ended_last_friendly_turn_with_defensive_fire_eligibility`. |
| `forced_retreat` | `MultiBinary(4)` | Core `forced_to_retreat_since_last_friendly_turn`. |
| `fire_spent` | `MultiBinary(4)` | Core `defensive_fire_spent_this_off_turn`. |
| `pending` | `MultiBinary(2)` | Learner slots still awaiting an order. |
| `remaining_cycles` | `Box(0, cycle_limit, (1,), int32)` | Budget including the current cycle. |

Total: **355 scalar inputs**, plus the separate **162-bit mask**. Dead/padding slots zero every per-unit field except dead slots retain `present=1`. At either ending, clear pending bits and the action mask, retaining actual final living-unit state. Early completion can retain positive budget; cutoff has zero. Shapes never change with casualties or supported roster size.

### Environment and player boundary

Expose `reset(seed)`/`step(action)` with the existing structural `Transition` fields and a thin Gym adapter with standard tuples and native `action_masks()`. Use `MaskablePPO` `MultiInputPolicy` prediction with the current mask; reject incompatible 1v1 policies before prediction. The lightweight environment/inspector must remain usable without trainer dependencies.
One `random.Random(seed)` drives opponent and core randomness. The opponent samples uniformly from sorted legal joint indexes after each resolved move (not uniformly by unit). Random learner play uses a separate RNG at that seed; hold chooses the lowest pending slot's current cell. Explicit Gym resets restart the seed sequence; automatic resets advance it as in 03. Seed the action space too.
Core `Player.movement() -> list[UnitMovementPlan]` returns a whole-turn batch before resolution, so it cannot observe first-mover fire before choosing another order. Use an explicit local driver, not a drop-in multi-unit `PPOPlayer`; do not mutate the game inside `movement()` or simulate future rolls to manufacture a batch. Incremental core-player integration requires later design.

## 5. Acceptance Criteria

- **AC-001 — Legal complete turns:** Either unit can act first. Every legal action has a core path; invalid actions/paths are non-mutating. Holds and interrupted moves consume exactly one order. Both slot orders finish learner movement before one joint combat phase and the opponent's complete turn; holds do not suppress combat.
- **AC-002 — Fire and order matter:** A controlled reversed-order replay shows the first mover receives a ready defender's shot, the next decision sees that defender spent, and it cannot fire again that turn. A fire-induced retreat or removal is reflected in the next inputs without reoffering the mover or running combat between choices.
- **AC-003 — Stable state:** Supported roster sizes, casualties (including surviving slot 1), and stacks retain the declared spaces, identities, pending bits, and exact core-derived masks. Unsupported configurations fail. Audit mutable movement/fire state against core, not cached pre-resolution values.
- **AC-004 — Endings:** Core win/loss/draw rewards and ending flags agree with authoritative status. A one-cycle cutoff completes all applicable turns, stays `in_progress`, and differs from a completion at the limit. Ending masks are false, counters respect the bound, and stepping requires reset afterward.
- **AC-005 — Replay and inspection:** Bounded random and hold rollouts repeat under matching seeds/actions, create fresh state on reset, and expose enough current inputs, chosen orders, core events, and endings to audit timing and legality. An inconsistency fails the inspection rather than merely printing a trace.
- **AC-006 — Policy compatibility:** An initialized CPU masked policy predicts legal joint actions with both slots pending, either slot alone, and a hold-only mask, without weight updates. Incompatible 1v1 inputs/policies are rejected, and existing server-side checks still pass.

## 6. Test Automation Strategy

Use focused `pytest` tests under `battle_agent_rl/tests/ppo`, real core transitions, and controlled RNG fixtures for the six gates. Verify public state/events rather than exact logs or private calls. Check `observation_space.contains` at decisions/endings; avoid an unmasked generic checker. Run `./server-side-checks.sh` after implementation. No training or statistical performance campaign is required.

## 7. Rationale & Context

| Design | Timing, masking, and tradeoff |
| --- | --- |
| **Chosen joint unit/destination** | Live fire feedback, 162 exactly masked logits, policy-controlled order, automatic turn completion. Sparse per-decision team credit, but no custom policy architecture. |
| Fixed-order per-unit | Same live timing and only 81 logits, but cannot choose who draws defensive fire. |
| Whole-turn orders | Fits `Player.movement()` and one credit transition per cycle; up to `81²=6561` joint choices. Independent destination masks cannot represent dependencies or subsequent fire effects. |
| Autoregressive batch | Linear output work with prefix context, but unresolved stochastic fire still prevents knowing later live legality; adds decoder/learning-interface complexity. |

All schemes need global unit state and padding for variable rosters. The chosen per-slot observation preserves identity, stacks, and readiness at modest `O(units * cells)` input size; it is not a variable-board solution. Automatic completion avoids an extra end-turn choice without restricting movement order.
The 9×9 interior starts reduce the edge pressure of 5×5, where failed two-hex retreats can dominate play. Core edge rules remain unchanged. One fixed layout still risks layout-specific behavior; varied starts, broader training, and generalization claims remain later work.

## 8. Dependencies & External Integrations

Use existing core game/movement/combat/unit interfaces and the existing CPU Gymnasium/NumPy/SB3-Contrib stack. Core stays independent of PPO dependencies; no external service is needed.

## 9. Examples & Edge Cases

Initial holds are `29` for slot 0 and `128` for slot 1. Choosing `128` first leaves `pending=[1,0]` and masks `81..161`; remaining movement points do not permit another order. If slot 0 later dies, slot 1 keeps that same action block. Stacked units at cell 40 have distinct holds `40` and `121`.

## 10. Validation Criteria

Deliver the prototype, a documented bounded inspection invocation, and evidence for the six gates. This proves the decision contract, not skill. Update completion status only after implementation and verified evidence; writing or revising this specification does not complete 06.

## 11. Related Specifications / Further Reading

[01 — Environment](01-training-environment.md) · [02 — Audit](02-rollout-inspection.md) · [03 — Masked PPO](03-masked-ppo-training.md) · [04 — Evaluation](04-evaluation-and-checkpoints.md) · [05 — Inference](05-inference-player.md) · [Schedule](implementation-schedule.md) · [PPO vision](../../battle_agent_rl/PPO.md)

## Open Questions

No questions.
