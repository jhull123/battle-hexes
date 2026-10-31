---
title: "PPO Agent 08: Crossroads Environment and Policy Contract"
date_created: 2026-10-31
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Make actual Crossroads the shared training/inference task, without transferring prototype weights or starting the training campaign.

## 1. Purpose & Scope

Implement [schedule 2, increment 08](playable-player-schedule.md#08--crossroads-environment-and-policy-contract) under `battle_agent_rl.ppo`. Support **PPO as Player 1 / Airborne**, versus **Human as Player 2 / Wehrmacht**. Use seeded random/hold controllers as non-learning verification substitutes for the human. Deliver the environment, shared conversion and live-turn contract, thin Gymnasium adapter, inspection, and compatibility plumbing. Campaign training/evaluation (09), evaluated frozen-player parity (10), and API/UI promotion (12) remain out of scope; preserve 07's playable slice and artifacts.

## 2. Definitions

- **PPO:** Proximal Policy Optimization, using existing SB3-Contrib `MaskablePPO`.
- **Slot:** Permanent scenario unit identity, never compacted after death or arrival.
- **Order:** One pending unit's destination choice, including hold at its current cell.
- **Cycle:** Both side turns; core turn number is authoritative.
- **Cutoff:** External stopping bound while core remains `in_progress`, not a draw.

## 3. Requirements, Constraints & Guidelines

- **REQ-001 — Task:** Load existing `d_day_crossroads`, version `"1"`, through core: 18×18, six Airborne, three initial Germans plus two reinforcements, stacking limit 2, three objectives, eight-turn limit. Preserve its units, terrain, roads, fire settings, victory rules and reinforcement rules; do not create a simplified training copy. Reject other scenarios, sides, rosters or gameplay fingerprints.
- **REQ-002 — Shared execution:** Reuse/extract 07's live-order workflow; separate scenario/encoding, turn orchestration, Gym adaptation, inspection and artifact validation. One order resolves movement and defensive fire/retreat through core before another prediction. Consume that unit's order even if it holds, retreats or dies. Close movement and resolve applicable combat once per side, then use core end-turn transitions. Keep pending IDs independent of remaining movement points. Never produce a precomputed whole-turn batch for PPO.
- **REQ-003 — Empty turns and arrivals:** Initialize pending from on-board units at each side's movement start, including zero-movement units with hold-only orders. Prune deaths. If no orders exist, close the side through the same core phase transitions without predicting or inventing a pass action; continue until a learner decision, completion or cutoff. Core may keep an empty side active for eligible reinforcements or objective scoring. Core deploys the turn-3 group, retries blocked entry, applies stacking and initializes fire readiness; never deploy/reset readiness in the encoder.
- **REQ-004 — Rules and reward:** Initialize scores through core at reset; thereafter use core's objective scorer in the shared workflow at ordinary-game scoring points, including after combat, before final turn-limit evaluation. Encoding must not score or evaluate victory. Scores are current control, not accumulated captures: Airborne scores occupied objectives; Wehrmacht scores every other objective. Read winner/reason from core, including its objective-conditioned elimination rules. Reward once at completion: win `+1`, loss `-1`, draw `0`; otherwise `0`, including cutoff. No reward shaping.
- **REQ-005 — Horizon:** `remaining_cycles = max(0, 9 - game.turn_number)` includes the current cycle and ignores external caps. Accept an external cycle cap of 1–8, default 8. Finish both applicable side turns before cutoff; core completion takes precedence. Core decides the end of turn 8. At completion/cutoff clear pending and masks, retain actual final state and true scenario horizon, and reject further steps until reset. Learner orders are bounded by 48 per episode.
- **CON-001:** Core remains the sole rules/scoring/completion authority and gains no PPO dependency. Preserve 5×5, 06 and 07 contracts; do not replace committed weights, change public player choices, add HTTP routes or migrate saved games in this increment.

## 4. Interfaces & Data Contracts

### Identity, actions and masks

Contract: **`battle-hexes-crossroads-airborne-unit-destination-live-turnlimit8-v1`**. Observation slots are Airborne A–F (`Airborne Inf. A` through `Airborne Inf. F`), followed by `A / Inf. Zug`, `B / Inf. Zug`, `Crossroads Feldwache`, `MG Trupp A`, `StuG. III Zug A`. Reserve reinforcement slots from reset; distinguish not-yet-deployed from eliminated. Stacks retain separate position rows.

Use `Discrete(1944)`: `action = slot * 324 + row * 18 + column`, where PPO slot is 0–5. A fresh `bool[1944]` mask enables exactly core-reachable destinations, including hold, for on-board pending Airborne units. Other blocks are false. Validate scalar integer (not boolean), bounds, current mask, core path/endpoints and current movement budget **before mutation**, including RNG consumption. Pending units must have their full first-order allowance; split orders are unsupported. Never replace an invalid prediction with hold. An all-false mask is permitted only at endings or internal automatic phase advancement, never at a policy call.

### Observation

Use fresh, unnormalized Gymnasium `Dict` arrays; row-major cells and the fixed slots above. Binary fields use `MultiBinary`; other fields use `Box` with the listed dtype/bounds. No future rolls, RNG state or hypothetical outcomes are inputs. Decisions occur only in Airborne movement, so actor/phase are fixed at this boundary.

| Field | Shape / dtype / bounds | Meaning |
| --- | --- | --- |
| `positions` | `[11,324] int8`, binary | One bit per on-board slot; all stack occupants retained. |
| `unit_status` | `[11] int8`, 0–2 | 0 awaiting deployment, 1 on board, 2 eliminated. |
| `unit_stats` | `[11,4] float32`, 0–7 | Attack, defense, full movement, defensive-fire modifier; retain for all slots. |
| `movement_remaining` | `[11] int8`, 0–7 | Live movement points; zero off-board. |
| `fire_flags` | `[11,4] int8`, binary | Public readiness relative to Airborne, last-friendly-turn eligibility, forced retreat, fire spent; zero off-board. |
| `pending` | `[6] int8`, binary | Airborne orders remaining, not movement allowance. |
| `terrain` | `[324,3] float32`, -2–3 | Core-resolved movement cost, defensive-fire modifier, combat odds shift, including defaults. |
| `road_edges` | `[324,6] float32`, 0–1 | Declared edge cost; 0 means no road/out-of-bounds. Direction order follows core's six neighbor offsets, without removing boundary directions. |
| `objective_points` | `[324] int8`, 0–1 | Scenario objective locations/points. |
| `objective_control` | `[3] int8`, binary | Airborne occupies objective, in scenario objective order. |
| `scores` | `[2] int8`, 0–3 | Already-computed core scores, Airborne then Wehrmacht. |
| `reinforcement` | `[1,4] int32`, 0–17 | Arrival turn, entry row, entry column, group status (0 scheduled, 1 delayed, 2 entered). |
| `remaining_cycles` | `[1] int32`, 0–8 | True eight-turn horizon, never the external inspection cap. |

Derive unit lifecycle from the fixed roster, core board and reinforcement-group state, not coordinates alone. Off-board positions are zero. The reinforcement group is `wehrmacht_stug_column`, due turn 3 at `(0,16)`; both reserved slots remain identifiable after entry/death. Road metadata is observable but **does not imply a movement discount**: current core movement uses destination terrain cost. Audit and preserve that behavior; road-rule changes require a separate rules decision and a new compatible task contract.

### Environment, randomness and artifacts

- Expose existing structural `reset(seed)` / `step(action)` transitions and thin Gymnasium tuples plus native `action_masks()`. Every non-ending return is a learner decision with a legal action. Aggregate all intervening fire, combat and reinforcement events into transition info, with decision count, scores, core status/reason and outcome (`win|loss|draw|cutoff`). Keep lightweight inspection usable without trainer libraries.
- Preserve the established RNG protocol: one seeded `random.Random` for core and opponent; random opponent samples sorted legal joint unit/destination indices after each live resolution. Its local slots are the five German slots. Hold orders lowest pending slot first. Random learner inspection uses a separate seeded RNG. Record seeds, actions, runtime and any external cap for replay.
- Adapt 07's trainer/environment and manifest interfaces through an explicit Crossroads task selection, not a second trainer or changes to 9×9 defaults. Record contract, scenario version/gameplay fingerprint, eight-turn horizon, PPO side, ordered slot IDs, exact spaces, reward definition, seed/configuration, runtime versions and checkpoint digest. Preserve existing trained-artifact evidence checks. Reject 5×5/9×9 artifacts and wrong side/rules/spaces **before prediction**; never relabel or transfer their weights. Initialized policies and temporary serialization fixtures are test-only, not serving checkpoints or training evidence. No campaign or production artifact is required in 08.

## 5. Acceptance Criteria

- **AC-001:** Fresh reset matches core-loaded Crossroads. Every input and mask matches audited live state before/after orders, fire, retreat, stacking, casualties and reinforcement arrival; shapes remain fixed.
- **AC-002:** Either friendly slot may act first; spent/dead slots cannot act again. Invalid actions leave game, pending, counters, events and RNG unchanged. Hold-only and no-unit turns progress legally without extra combat or empty-mask prediction.
- **AC-003:** Unblocked reinforcements arrive on turn 3 with reserved identities and correct readiness; blocked entry delays/retries under core. No on-board German units with eligible pending arrivals does not cause a fabricated elimination result.
- **AC-004:** Audited random/hold games reach core completion, including objective-based turn-8 results. Rewards, scores and flags agree with core. A smaller external cap remains a cutoff with the true horizon; completion on the bound wins precedence.
- **AC-005:** A compatible initialized masked policy chooses legal actions on reachable Crossroads states, including one-unit and hold-only masks. Contract/side/space mismatches reject before prediction; existing 07 games/artifacts still work.
- **AC-006:** A local Human-controlled Wehrmacht driver and the non-learning opponent adapter use the same shared core turn/scoring semantics and live state conversion. Scripted legal human orders suffice here; browser acceptance remains 12.

## 6. Test Automation Strategy

Use `pytest` under `battle_agent_rl/tests/ppo`, real core transitions and controlled RNG/state fixtures for blocked arrivals, empty turns, fire/retreat and ending precedence. Check `observation_space.contains`, mask/path equivalence and matching seeded action/event replays. Do not depend on random seeds alone to encounter edge cases. Run `./server-side-checks.sh` after implementation; no web/e2e or strength gate is required.

## 7. Rationale & Context

Six live unit/destination blocks preserve 07's policy-controlled order and fire feedback. Fixed global inputs expose heterogeneous units, objective incentives and pending arrivals without requiring a variable-board architecture. Sparse terminal rewards preserve the actual game objective; policy strength is a later gate.

## 8. Dependencies & External Integrations

Core scenario loader, movement, scoring, reinforcement and phase APIs; 07's live resolution and training/artifact interfaces; existing CPU NumPy/Gymnasium/PyTorch/SB3-Contrib stack. No new service or API/UI integration.

## 9. Examples & Edge Cases

- Initial Airborne A at `(12,11)` holds with action `227`; F at `(16,7)` holds with `1915`. Either consumes only that slot's order.
- At turn 3 the two Germans may stack at `(0,16)` only if core permits the entire group. Occupied/blocked entry leaves both pending, not dead.
- If all Airborne die but Germans have not met core's victory condition, advance empty Airborne turns until core completes; do not fabricate a terminal loss. Two occupied objectives at the turn limit score Airborne 2, Wehrmacht 1.

## 10. Validation Criteria

Deliver AC-001–AC-006, a repeatable bounded inspection command, a concise input/mask audit and seed/action traces covering arrival and objective completion. Only after implementation and verified evidence update the schedule and `PPO.md`; this specification alone leaves 08 planned.

## 11. Related Specifications / Further Reading

[07 — Playable slice](07-trained-9x9-human-visible-slice.md) · [06 — Multi-unit contract](06-multi-unit-design.md) · [API integration boundary](spec-architecture-game-agent-integration-boundary.md) · [Active schedule](playable-player-schedule.md) · [PPO status](../../battle_agent_rl/PPO.md)

## Open Questions

No questions.
