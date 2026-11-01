---
title: "PPO Agent 08: Crossroads Environment and Policy Contract"
date_created: 2026-10-31
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Make actual Crossroads the shared training/inference task, without transferring prototype weights or starting the training campaign.

## 1. Purpose & Scope

Implement [schedule 2, increment 08](playable-player-schedule.md#08--crossroads-environment-and-policy-contract) under `battle_agent_rl.ppo`. Support **PPO as Player 2 / Wehrmacht**, versus **Human as Player 1 / Airborne**. Preserve core player order: Airborne first, Wehrmacht second. Use seeded random/hold controllers as non-learning verification substitutes for the human. Deliver the environment, shared conversion and live-turn contract, thin Gymnasium adapter, inspection, and compatibility plumbing. Campaign training/evaluation (09), evaluated frozen-player parity (10), and API/UI promotion (12) remain out of scope; preserve 07's first-seat PPO behavior and artifacts. **08 remains planned.**

## 2. Definitions

- **PPO:** Proximal Policy Optimization, using existing SB3-Contrib `MaskablePPO`.
- **Slot:** Permanent scenario unit identity, never compacted after elimination or arrival.
- **Order:** One pending unit's destination choice, including hold at its current cell.
- **Cycle:** Airborne's turn followed by Wehrmacht's turn; core turn number is authoritative, not a learner-first cycle.
- **Cutoff:** External stopping bound while core remains `in_progress`, not a draw.

## 3. Requirements, Constraints & Guidelines

- **REQ-001 — Task:** Load existing `d_day_crossroads`, version `"1"`, through core: 18×18, six Airborne, three initial Germans plus two reinforcements, stacking limit 2, three objectives, eight-turn limit. Preserve its units, terrain, roads, fire settings, victory rules and reinforcement rules; do not create a simplified training copy. Reject other scenarios, sides, rosters or gameplay fingerprints.
- **REQ-002 — Shared execution:** Reuse/extract 07's live-order workflow; separate scenario/encoding, turn orchestration, Gym adaptation, inspection and artifact validation. One order resolves movement and defensive fire/retreat through core before another prediction. Consume that unit's order even if it holds, retreats or is eliminated. Close movement and resolve applicable combat once per side, then use core end-turn transitions. Keep pending IDs independent of remaining movement points. Never produce a precomputed whole-turn batch for PPO.
- **REQ-003 — Empty turns and arrivals:** Initialize pending from on-board units at each side's movement start, including the zero-movement Feldwache with a hold-only order. Remove eliminated units from pending. If no orders exist, close the side through the same core phase transitions without predicting or inventing a pass action; continue until a learner decision, completion or cutoff. Core may keep an empty side active for eligible reinforcements or objective scoring. Reinforcements deploy on the cycle wrap into turn 3, **before Airborne moves**; blocked groups retry on later wraps, not at the Wehrmacht handoff. New units may be attacked/retreated/eliminated before their first PPO decision. Core owns deployment, stacking, movement resets and fire eligibility; never deploy/reset readiness in the encoder.
- **REQ-004 — Rules and reward:** Initialize scores through core at reset; thereafter use core's objective scorer in the shared workflow at ordinary-game scoring points, including after combat, before final turn-limit evaluation. Encoding must not score or evaluate victory. Keep `scoring_side=Airborne`: Airborne scores occupied objectives; Wehrmacht scores every other objective, including empty ones. Scores are current control, not accumulated captures. Read winner/reason from core; Wehrmacht does not gain Airborne's early-elimination victory condition. Reward once at completion **relative to Wehrmacht**: Wehrmacht win `+1`, Airborne win `-1`, draw `0`; otherwise `0`, including cutoff and nonterminal elimination. No reward shaping.
- **REQ-005 — Horizon:** `remaining_cycles = max(0, 9 - game.turn_number)` includes the current cycle and ignores external caps. Accept an external cycle cap of 1–8, default 8. Check cutoff after Wehrmacht ends the capped cycle, **before Airborne acts next**; core completion takes precedence. A normal core end-turn may already have advanced the turn/deployed the next cycle's reinforcements; retain that state, without extra opponent movement. Core decides turn 8 at the end of Wehrmacht's turn. At completion/cutoff clear pending and masks, retain actual final state and true scenario horizon, and reject further steps until reset. At most 36 learner orders occur: three per cycle in turns 1–2, at most five in turns 3–8.
- **CON-001:** Core remains the sole rules/scoring/completion authority and gains no PPO dependency. Preserve 5×5, 06 and 07 contracts; do not replace committed weights, change public player choices, add HTTP routes or migrate saved games in this increment.

## 4. Interfaces & Data Contracts

### Identity, actions and masks

Contract: **`battle-hexes-crossroads-wehrmacht-unit-destination-live-turnlimit8-v1`**. Observation slots 0–4 are `A / Inf. Zug`, `B / Inf. Zug`, `Crossroads Feldwache`, `MG Trupp A`, `StuG. III Zug A`; slots 5–10 are Airborne A–F (`Airborne Inf. A` through `Airborne Inf. F`). Observation order is learner-first; **core player order is unchanged**. Reserve reinforcement slots 3–4 from reset; never compact/reuse them after arrival/elimination. Stacks retain separate position rows.

Use `Discrete(1620)`: `action = slot * 324 + row * 18 + column`, where PPO slot is 0–4. A fresh `bool[1620]` mask enables exactly core-reachable destinations, including hold, for on-board pending Wehrmacht units. Awaiting, eliminated and already-ordered blocks are false. Validate scalar integer (not boolean), bounds, current mask, core path/endpoints and current movement budget **before mutation**, including RNG consumption. Pending units must have their full first-order allowance; split orders are unsupported. Never replace an invalid prediction with hold. An all-false mask is permitted only at endings or internal automatic phase advancement, never at a policy call.

### Observation

Use fresh, unnormalized Gymnasium `Dict` arrays; row-major cells and the fixed slots above. Binary fields use `MultiBinary`; other fields use `Box` with the listed dtype/bounds. No future rolls, RNG state or hypothetical outcomes are inputs. Decisions occur only in Wehrmacht movement, **after that cycle's Airborne movement/combat**, so actor/phase are fixed at this boundary.

| Field | Shape / dtype / bounds | Meaning |
| --- | --- | --- |
| `positions` | `[11,324] int8`, binary | One bit per on-board slot; all stack occupants retained. |
| `unit_status` | `[11] int8`, 0–2 | 0 awaiting deployment, 1 on board, 2 eliminated. |
| `unit_stats` | `[11,4] float32`, 0–7 | Attack, defense, full movement, defensive-fire modifier; retain for all slots. |
| `movement_remaining` | `[11] int8`, 0–7 | Live movement points; zero off-board. |
| `fire_flags` | `[11,4] int8`, binary | Public readiness relative to Wehrmacht, last-friendly-turn eligibility, forced retreat, fire spent; zero off-board. |
| `pending` | `[5] int8`, binary | Wehrmacht orders remaining, not movement allowance; includes surviving arrivals at their first friendly movement start. |
| `terrain` | `[324,3] float32`, -2–3 | Core-resolved movement cost, defensive-fire modifier, combat odds shift, including defaults. |
| `road_edges` | `[324,6] float32`, 0–1 | Declared edge cost; 0 means no road/out-of-bounds. Direction order follows core's six neighbor offsets, without removing boundary directions. |
| `objective_points` | `[324] int8`, 0–1 | Scenario objective locations/points. |
| `objective_control` | `[3] int8`, binary | **Airborne** occupies objective, in scenario objective order; 0 credits Wehrmacht even if empty. |
| `scores` | `[2] int8`, 0–3 | Already-computed core scores, **Wehrmacht then Airborne** (learner-first, not core player order). |
| `reinforcement` | `[1,4] int32`, 0–17 | Arrival turn, entry row, entry column, group status (0 scheduled, 1 delayed, 2 entered). |
| `remaining_cycles` | `[1] int32`, 0–8 | True eight-turn horizon, never the external inspection cap. |

Derive unit lifecycle from the fixed roster, core board and reinforcement-group state, not coordinates alone. Off-board positions are zero. The reinforcement group is `wehrmacht_stug_column`, due turn 3 at `(0,16)`; group status follows core's scheduled/delayed/entered state, independently of later unit eliminations. Arrivals cannot fire defensively during the intervening Airborne turn until their first friendly turn has ended; encode core's public readiness at each actual decision, not a cached arrival flag. Road metadata is observable but **does not imply a movement discount**: current core movement uses destination terrain cost. Audit and preserve that behavior; road-rule changes require a separate rules decision and a new compatible task contract.

### Environment, randomness and artifacts

- Use `MaskablePPO("MultiInputPolicy", ...)` with explicit `policy_kwargs={"net_arch": {"pi": [64, 64], "vf": [64, 64]}}` for the initial Crossroads baseline: separate two-layer policy/value networks, default `Tanh` activations, and the default flatten-and-concatenate extractor for these non-image observations. Apply this configuration to 08's initialized-policy checks and the initial 09 training baseline; preserve 07's existing architecture and artifacts. No custom feature extractor is required initially.
- Expose existing structural `reset(seed)` / `step(action)` transitions and thin Gymnasium tuples plus native `action_masks()`. In the non-learning environment, reset creates core with Airborne first, resolves its opening turn using the substitute controller, then returns the first Wehrmacht decision (zero learner orders). Within a PPO turn, step returns after the chosen order's live effects. Its final order also closes Wehrmacht's turn; if active and below the cap, resolve the next Airborne turn before returning the next Wehrmacht decision. Stop immediately on core completion, including during Airborne actions; never predict afterward. Empty-turn advancement follows REQ-003. Every non-ending return is a learner decision with a legal action.
- Aggregate all intervening fire, combat and reinforcement events into transition info, including reset's opening Airborne events, with learner-order count, scores, core status/reason and Wehrmacht-relative outcome (`win|loss|draw|cutoff`). In the local human driver, await explicit first-seat human commands instead of automatically acting for them; invoke PPO only after core hands off to Wehrmacht. Keep lightweight inspection usable without trainer libraries.
- Preserve the established RNG protocol: one seeded `random.Random` for core and opponent; random opponent samples sorted legal joint unit/destination indices after each live resolution. Its local slots are the six Airborne units A–F, with 1944 local indices (not the PPO action space). Hold orders lowest pending slot first. Random learner inspection uses a separate seeded RNG. Record seeds, opening opponent actions, subsequent actions, runtime and any external cap for replay.
- Adapt 07's trainer/environment and manifest interfaces through an explicit Crossroads task selection, not a second trainer or changes to 9×9 defaults. Record contract, scenario version/gameplay fingerprint, eight-turn horizon, PPO side (`Player 2` / `Wehrmacht`), core player order, ordered slot IDs, exact spaces, reward definition, seed/configuration, runtime versions and checkpoint digest. Preserve existing trained-artifact evidence checks. Reject the superseded Airborne draft contract, 5×5/9×9 artifacts and wrong side/rules/spaces **before prediction**; never relabel or transfer their weights. Initialized policies and temporary serialization fixtures are test-only, not serving checkpoints or training evidence. No campaign or production artifact is required in 08.

## 5. Acceptance Criteria

- **AC-001:** Core starts with Airborne; reset's first policy state follows its complete opening turn, with zero learner orders and `remaining_cycles=[8]`. Every input and mask matches audited live state before/after orders, fire, retreat, stacking, casualties and arrivals, using the five-German/six-Airborne slot order and Wehrmacht public-fire perspective. Shapes remain fixed.
- **AC-002:** Any pending German slot may act first; Feldwache is hold-only. Spent/eliminated/awaiting slots cannot act. Invalid actions leave game, pending, counters, events and RNG unchanged. Empty German turns advance without extra combat or empty-mask prediction. Final orders resolve Wehrmacht once, then Airborne once before the next decision unless completed/capped; completion during Airborne yields a terminal transition without another prediction.
- **AC-003:** Unblocked reinforcements arrive before Airborne's turn 3 and can be affected by that turn; they cannot fire defensively during it. Surviving arrivals use slots 3–4 at Wehrmacht's movement start with core movement/fire state; eliminated arrivals stay eliminated. Blocked entry retries only on subsequent cycle wraps. No on-board Germans with eligible pending arrivals does not cause a fabricated elimination result.
- **AC-004:** Audited random/hold games reach core completion, including objective-based results at the end of Wehrmacht's turn 8. Wehrmacht win/loss rewards are `+1/-1`; scores retain Airborne's occupation rule. An earlier cap stops after Wehrmacht, before the next Airborne action, with core `in_progress` and true horizon; completion on the bound takes precedence. Nonterminal elimination is not rewarded as completion.
- **AC-005:** A compatible initialized policy selects legal actions under the 1620-bit mask on reachable three-/five-unit, one-unit and hold-only states. Superseded Airborne draft, contract/side/space mismatches reject before prediction; existing 07 first-seat games/artifacts remain unchanged.
- **AC-006:** A local Human-controlled Airborne driver and its non-learning substitute use the same core turn/scoring semantics and conversion. Human acts first; PPO waits for second-seat movement. Scripted legal human orders suffice here; browser acceptance remains 12.

## 6. Test Automation Strategy

Use `pytest` under `battle_agent_rl/tests/ppo`, real core transitions and controlled RNG/state fixtures for blocked arrivals, empty turns, fire/retreat and ending precedence. Check `observation_space.contains`, mask/path equivalence and matching seeded action/event replays. Do not depend on random seeds alone to encounter edge cases. Run `./server-side-checks.sh` after implementation; no web/e2e or strength gate is required.

## 7. Rationale & Context

Five live unit/destination blocks preserve 07's policy-controlled order and fire feedback while supporting Wehrmacht's three initial units and two arrivals. Learner-first arrays do not reorder core turns or change Airborne's scoring rule. Fixed global inputs expose heterogeneous units, objective incentives and pending arrivals; sparse Wehrmacht-relative terminal rewards preserve the actual objective. Policy strength is a later gate.

## 8. Dependencies & External Integrations

Core scenario loader, movement, scoring, reinforcement and phase APIs; 07's live resolution and training/artifact interfaces; existing CPU NumPy/Gymnasium/PyTorch/SB3-Contrib stack. No new service or API/UI integration.

## 9. Examples & Edge Cases

- After an opening Airborne hold turn, German A at `(3,15)` holds with `69`, B at `(4,5)` with `401`, and Feldwache at `(6,9)` with `765` (its only action). Slots 3–4 are masked until deployment; each order consumes only its own slot. No objective is Airborne-occupied: learner-first `scores=[3,0]`.
- On the wrap into turn 3, MG and StuG may stack at `(0,16)` only if core permits the entire group. Blocked entry leaves both awaiting deployment, not eliminated. If still there at Wehrmacht's movement start, their distinct holds are `988` and `1312`; their first observation includes Airborne's intervening actions.
- If all Airborne units are eliminated, do not fabricate an immediate Wehrmacht win: core can continue through empty Airborne turns to objective scoring. Two Airborne-occupied objectives at the turn limit score Airborne 2, Wehrmacht 1: PPO loss/reward `-1`. Zero Airborne-occupied objectives score Wehrmacht 3, Airborne 0: PPO win/reward `+1`, even for empty objectives.
- A cap after Wehrmacht's turn 2 returns cutoff before Airborne moves on turn 3; core's normal wrap may already deploy reinforcements. `remaining_cycles=[6]`, not zero, and no arrival receives a PPO order after cutoff.

## 10. Validation Criteria

Deliver AC-001–AC-006, a repeatable bounded inspection command, a concise input/mask audit and seed/action traces covering arrival and objective completion. Only after implementation and verified evidence update the schedule and `PPO.md`; this specification alone leaves 08 planned.

## 11. Related Specifications / Further Reading

[07 — Playable slice](07-trained-9x9-human-visible-slice.md) · [06 — Multi-unit contract](06-multi-unit-design.md) · [API integration boundary](spec-architecture-game-agent-integration-boundary.md) · [Active schedule](playable-player-schedule.md) · [PPO status](../../battle_agent_rl/PPO.md)

Core contract references: [Crossroads scenario](../../battle_hexes_core/src/battle_hexes_core/scenarios/d_day_crossroads.json), [turn transitions](../../battle_hexes_core/src/battle_hexes_core/game/game.py), [reinforcement deployment](../../battle_hexes_core/src/battle_hexes_core/game/reinforcements_deployer.py), [scoring](../../battle_hexes_core/src/battle_hexes_core/scoring/objective_scorer.py), [completion](../../battle_hexes_core/src/battle_hexes_core/scoring/game_status_evaluator.py).

## Open Questions

No questions.
