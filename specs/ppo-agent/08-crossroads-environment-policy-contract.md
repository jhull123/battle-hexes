---
title: "PPO Agent 08: Crossroads Environment and Policy Contract"
date_created: 2026-10-31
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Make actual Crossroads the shared training/inference task, without transferring prototype weights or starting the training campaign.

## 1. Purpose & Scope

Implement [schedule 2, increment 08](playable-player-schedule.md#08--crossroads-environment-and-policy-contract) under `battle_agent_rl.ppo`. Support **PPO as Player 2 / Wehrmacht**, versus **Human as Player 1 / Airborne**. Preserve core player order: Airborne first, Wehrmacht second. Use seeded random/hold controllers as non-learning verification substitutes for the human. Deliver the environment, shared conversion and live-turn contract, thin Gymnasium adapter, inspection, and compatibility plumbing. Campaign training/evaluation (09), evaluated frozen-player parity (10), and API/UI promotion (12) remain out of scope; preserve 07's first-seat PPO behavior and artifacts. **08 remains incomplete.**

### Delivery sequence

Implement these chunks in order; each extends the same data-driven machinery.

| Chunk | Status | Deliverable | Acceptance gate |
| --- | --- | --- | --- |
| **08a — State/action interface** | Merged in [#400](https://github.com/jhull123/battle-hexes/pull/400) | Scenario loading/binding, stable slots, derived bounds/spaces, observations, masks and action conversion. | [Partial audit](evidence/08-state-action-audit.md): unregistered-scenario lifecycle coverage and preserved Crossroads behavior. |
| **08b — Executable environment** | **Implemented and verified** | Reset/step, live orders, opponent/empty turns, core scoring/completion, rewards/cutoffs and non-learning inspection. | [Execution evidence](evidence/08-executable-environment.md): AC-001–AC-004 through production environment paths, controlled edge cases and repeatable random/hold completion/cutoff traces. |
| **08c — Policy integration** | Planned; after 08b | Thin Gym adapter, initialized masked-policy checks, trainer/artifact compatibility plumbing and scripted human driver. | AC-005–AC-006, bounded training/reload smoke and retained AC-001–AC-004 regressions. |

08b enables complete non-learning games; 08c enables short PPO training smoke
runs. Smoke checks prove plumbing, not strength; training/evaluation campaigns
remain increment 09. Increment 08 completes only when all three chunks and
AC-001–AC-006 pass; 06/07 contracts and artifacts remain unchanged.

08b's production entry points are `scenario_environment.ScenarioEnvironment`
and `python -m battle_agent_rl.ppo.scenario_inspection`. Both accept a
scenario-derived task with explicit learner selection; no scenario registry or
Crossroads engine facade was added. `live_turn` extracts the existing 07
live-order/phase workflow, with ordinary core scoring enabled by the new
environment. Gym/policy/trainer/artifact integration and the human driver remain
08c; increment 08 is **not complete**.

## 2. Definitions

- **PPO:** Proximal Policy Optimization, using existing SB3-Contrib `MaskablePPO`.
- **Slot:** Permanent scenario unit identity, never compacted after elimination or arrival.
- **Order:** One pending unit's destination choice, including hold at its current cell.
- **Cycle:** Airborne's turn followed by Wehrmacht's turn; core turn number is authoritative, not a learner-first cycle.
- **Cutoff:** External stopping bound while core remains `in_progress`, not a draw.

## 3. Requirements, Constraints & Guidelines

- **REQ-001 — Task:** Load existing `d_day_crossroads` through core, without a simplified training copy or exact-scenario lock. Its current version `"1"` defines 18×18, six Airborne, three initial Germans plus two reinforcements, stacking limit 2, three objectives and an eight-turn limit. These are scenario facts, not Python task constants or equality gates. Derive roster membership/ownership, dimensions, objectives, reinforcement groups, horizon and observation bounds from the loaded definition. The state/action layer must also accept differently named scenario data, including new JSON files loaded by ID/directory through core, without Python edits, registration or scenario-specific classes/modules. Reject actual representation limits and incompatible model interfaces, not changed gameplay data as such.
- **REQ-002 — Shared execution:** Reuse/extract 07's live-order workflow; separate scenario/encoding, turn orchestration, Gym adaptation, inspection and artifact validation. One order resolves movement and defensive fire/retreat through core before another prediction. Consume that unit's order even if it holds, retreats or is eliminated. Close movement and resolve applicable combat once per side, then use core end-turn transitions. Keep pending IDs independent of remaining movement points. Never produce a precomputed whole-turn batch for PPO.
- **REQ-003 — Empty turns and arrivals:** Initialize pending from on-board units at each side's movement start, including the zero-movement Feldwache with a hold-only order. Remove eliminated units from pending. If no orders exist, close the side through the same core phase transitions without predicting or inventing a pass action; continue until a learner decision, completion or cutoff. Core may keep an empty side active for eligible reinforcements or objective scoring. Reinforcements deploy on the cycle wrap into turn 3, **before Airborne moves**; blocked groups retry on later wraps, not at the Wehrmacht handoff. New units may be attacked/retreated/eliminated before their first PPO decision. Core owns deployment, stacking, movement resets and fire eligibility; never deploy/reset readiness in the encoder.
- **REQ-004 — Rules and reward:** Initialize scores through core at reset; thereafter use core's objective scorer in the shared workflow at ordinary-game scoring points, including after combat, before final turn-limit evaluation. Encoding must not score or evaluate victory. Keep `scoring_side=Airborne`: Airborne scores occupied objectives; Wehrmacht scores every other objective, including empty ones. Scores are current control, not accumulated captures. Read winner/reason from core; Wehrmacht does not gain Airborne's early-elimination victory condition. Reward once at completion **relative to Wehrmacht**: Wehrmacht win `+1`, Airborne win `-1`, draw `0`; otherwise `0`, including cutoff and nonterminal elimination. No reward shaping.
- **REQ-005 — Horizon:** `remaining_cycles = max(0, scenario.turn_limit + 1 - game.turn_number)` includes the current cycle and ignores external caps. The planned driver accepts an external cycle cap from 1 through the loaded horizon, defaulting to that horizon (currently 8). Check cutoff after Wehrmacht ends the capped cycle, **before Airborne acts next**; core completion takes precedence. A normal core end-turn may already have advanced the turn/deployed the next cycle's reinforcements; retain that state, without extra opponent movement. Core decides the final cycle at the end of Wehrmacht's turn. At completion/cutoff clear pending and masks, retain actual final state and true scenario horizon, and reject further steps until reset. The current scenario permits at most 36 learner orders: three per cycle in turns 1–2, at most five in turns 3–8; this is an example, not an implementation bound.
- **CON-001:** Core remains the sole rules/scoring/completion authority and gains no PPO dependency. Preserve 5×5, 06 and 07 contracts; do not replace committed weights, change public player choices, add HTTP routes or migrate saved games in this increment.
- **CON-002 — Reuse boundary:** Use **scenario data plus runtime learner selection; shared decision machinery**. Crossroads must not require a named Python definition or facade. Select the learner seat in runtime/training configuration; keep the interface version in shared implementation, independent of scenario identity. Read identity/version from the loaded definition; derive ordered rosters, bounds and decision configuration rather than duplicating gameplay data. Shared roster binding, spaces, observation encoding, pending masks and action conversion take explicit configuration: no scenario registry, name conditionals, named factions/units, fixed slot counts, board dimensions, single-group assumption or eight-turn horizon. Do not add environment orchestration, a parallel trainer, variable-roster neural architectures or automatic cross-scenario checkpoint compatibility in 08a. Data-driven loading does not establish policy generalization or multi-scenario training; preserve 06/07 contracts and artifacts.

## 4. Interfaces & Data Contracts

### Implementation responsibilities

- **Task interface / scenario compatibility:** `scenario_task.ScenarioTask(scenario_data, learner_seat)` accepts core-loaded `ScenarioData`; `ScenarioTask.load(scenario_id, learner_seat=..., scenario_dir=...)` uses the existing core JSON loader. The learner seat is required and the interface version is shared, not supplied per scenario. A task copies its input snapshot and derives ownership, complete rosters, resolved terrain/defaults and bounds through core. `task.create_game(rng)` returns a binding over raw core state without scoring or advancing; `task.bind_game(game, learner=None)` binds raw or advanced games by structural limits, optionally checking a supplied runtime learner. It does not construct a reference game for gameplay equality. `task.spec`, `task.scenario_id`, `task.scenario_version` and `task.contract` expose provenance/interface; `task.observation_space()` / `task.action_space()` use that same derived spec. Scenario edits require a new task, not per-call overrides of an existing spec. The Crossroads forwarding modules and `scenario_binding` are removed rather than replaced with forwarding modules or a registry.
- **Decision machinery:** `decision_contract`, `decision_binding`, `decision_observation` and `decision_actions` own configured dimensions/bounds, permanent identities, public-state arrays, legal pending-order masks and validated conversion. Reinforcement rows follow scenario group IDs, including zero/multiple groups; omitting entered groups from core's pending menu must not shift identities/statuses.
- **Roles:** learner/opponent derive from the configured learner seat, without reordering core players. Resolve the objective scoring player independently from core's `victory.scoring_side`; `objective_control` means that player's occupation, while `scores` remain learner then opponent. For this task that still means Airborne control and Wehrmacht-first scores. Encoding never computes scores, victory or transitions.

### Interface version and compatibility

The interface label is now **`battle-hexes-unit-destination-live-v2`**, replacing
`battle-hexes-crossroads-wehrmacht-unit-destination-live-turnlimit8-v1`.
This explicitly changes the configuration contract: spaces/bounds and identities
are derived from the scenario, and the label no longer promises one horizon or
roster. There are no Crossroads weights to migrate. For the current checked-in
scenario, all thirteen fields, shapes, dtypes, bounds, identities and action
indices below remain numerically unchanged. That regression is **not** a claim
of model compatibility across scenario variations. Future model binding must
check the concrete spaces, ordered IDs, learner seat and interface semantics;
the version label alone cannot authorize reuse. No universal policy, environment,
new orchestration or artifact integration is delivered by 08a.

Supported inputs require two core players, a nonempty complete roster for each
role, unique unit identities, positive board dimensions and a finite positive
turn limit. Each scenario unit must have a core identity (initial deployment or
reinforcement); orphan roster entries cannot be represented. Objective inputs
require core's `objective_control` rule with an unambiguous scoring player.
Nonnegative unit stats, movement, road costs and objective points must fit the
declared dtypes: movement, per-cell point sums and total possible scores fit
`int8` (0–127); horizon, entry coordinates and arrival turns fit `int32`;
floating inputs are finite and fit `float32`. Terrain movement costs are positive
and fire modifiers nonnegative. Core retains relationship/rule validation.
Live binding checks configured dimensions/horizon, complete slot identities and
owners, objective coordinates, reinforcement IDs and numeric bounds. It does not
compare fire settings, full terrain/road layouts or other gameplay to an exact
Crossroads reference. Changes within that interface are permitted, not evidence
of a policy's skill or suitability.

### Identity, actions and masks

Slots are learner-first, then opponent, with each side's **complete scenario roster sorted lexicographically by unit ID**, including undeployed reinforcements. Sorting is case-sensitive Python string ordering, independent of JSON insertion order, deployment order or current board population. Build once for the scenario/episode; never compact/reuse slots after arrival/elimination. A scenario edit can change the next episode's mapping and must not silently reinterpret an existing policy. For current Crossroads, observation slots 0–4 remain `A / Inf. Zug`, `B / Inf. Zug`, `Crossroads Feldwache`, `MG Trupp A`, `StuG. III Zug A`; slots 5–10 remain Airborne A–F (`Airborne Inf. A` through `Airborne Inf. F`). **Core player order is unchanged**. Reserve reinforcement slots 3–4 from reset; stacks retain separate position rows.

Use `Discrete(learner_roster_size * rows * columns)` and `action = slot * (rows * columns) + row * columns + column`. Current Crossroads therefore retains `Discrete(1620)`, `action = slot * 324 + row * 18 + column`, where PPO slot is 0–4. A fresh Boolean mask enables exactly core-reachable destinations, including hold, for on-board pending learner units. Awaiting, eliminated and already-ordered blocks are false. Validate scalar integer (not boolean), bounds, current mask, core path/endpoints and current movement budget **before mutation**, including RNG consumption. Pending units must have their full first-order allowance; split orders are unsupported. Never replace an invalid prediction with hold. An all-false mask is permitted only at endings or internal automatic phase advancement, never at a policy call.

### Observation

Use fresh, unnormalized Gymnasium `Dict` arrays; row-major cells and the fixed slots above. Binary fields use `MultiBinary`; other fields use `Box` with the listed dtype/bounds. No future rolls, RNG state or hypothetical outcomes are inputs. Decisions occur only in Wehrmacht movement, **after that cycle's Airborne movement/combat**, so actor/phase are fixed at this boundary.

The table is the current Crossroads instance, not duplicated task configuration.
Derive scalar upper bounds from maximum complete-roster stats/movement, resolved
board terrain values, declared road costs, per-cell objective point sums and
core's objective-count score ceiling. Current core `objective_control` counts
objectives regardless of their declared point values; encoding never substitutes
weighted scoring. Terrain bounds include zero; reinforcement bounds cover
status 2, board coordinate maxima and all declared arrival turns/entry coordinates.
Horizon comes directly from the definition. Empty objective/group lists produce
empty arrays through the same machinery.

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
- Adapt 07's trainer/environment and manifest interfaces through an explicit Crossroads task selection, not a second trainer or changes to 9×9 defaults. Record interface version, loaded scenario identity/version and configuration provenance, derived horizon, PPO seat, core player order, ordered slot IDs, exact spaces, reward definition, seed/configuration, runtime versions and checkpoint digest. Preserve 06/07's existing artifact checks unchanged. Reject superseded contracts, 5×5/9×9 artifacts and incompatible side/slot mapping/spaces **before prediction**; never relabel or transfer their weights. Do not add an exact-gameplay rejection gate to this state/action delivery. Initialized policies and temporary serialization fixtures are test-only, not serving checkpoints or training evidence. No campaign or production artifact is required in 08.

## 5. Acceptance Criteria

- **AC-001:** Core starts with Airborne; reset's first policy state follows its complete opening turn, with zero learner orders and `remaining_cycles=[8]`. Every input and mask matches audited live state before/after orders, fire, retreat, stacking, casualties and arrivals, using the five-German/six-Airborne slot order and Wehrmacht public-fire perspective. Shapes remain fixed.
- **AC-002:** Any pending German slot may act first; Feldwache is hold-only. Spent/eliminated/awaiting slots cannot act. Invalid actions leave game, pending, counters, events and RNG unchanged. Empty German turns advance without extra combat or empty-mask prediction. Final orders resolve Wehrmacht once, then Airborne once before the next decision unless completed/capped; completion during Airborne yields a terminal transition without another prediction.
- **AC-003:** Unblocked reinforcements arrive before Airborne's turn 3 and can be affected by that turn; they cannot fire defensively during it. Surviving arrivals use slots 3–4 at Wehrmacht's movement start with core movement/fire state; eliminated arrivals stay eliminated. Blocked entry retries only on subsequent cycle wraps. No on-board Germans with eligible pending arrivals does not cause a fabricated elimination result.
- **AC-004:** Audited random/hold games reach core completion, including objective-based results at the end of Wehrmacht's turn 8. Wehrmacht win/loss rewards are `+1/-1`; scores retain Airborne's occupation rule. An earlier cap stops after Wehrmacht, before the next Airborne action, with core `in_progress` and true horizon; completion on the bound takes precedence. Nonterminal elimination is not rewarded as completion.
- **AC-005:** A compatible initialized policy selects legal actions under the 1620-bit mask on reachable three-/five-unit, one-unit and hold-only states. Superseded Airborne draft, contract/side/space mismatches reject before prediction; existing 07 first-seat games/artifacts remain unchanged.
- **AC-006:** A local Human-controlled Airborne driver and its non-learning substitute use the same core turn/scoring semantics and conversion. Human acts first; PPO waits for second-seat movement. Scripted legal human orders suffice here; browser acceptance remains 12.

## 6. Test Automation Strategy

Use `pytest` under `battle_agent_rl/tests/ppo`, real core transitions and controlled RNG/state fixtures for blocked arrivals, empty turns, fire/retreat and ending precedence. Check `observation_space.contains`, mask/path equivalence and matching seeded action/event replays. Do not depend on random seeds alone to encounter edge cases. Run `./server-side-checks.sh` after implementation; no web/e2e or strength gate is required.

For the state/action extraction, retain concrete Crossroads regression/space
checks and add data-driven tests with materially different
dimensions, roster, learner seat, scoring-side assignment and group count.
Exercise the same binding/encoding/mask/conversion implementations, not copies.
Load a differently named JSON file from a temporary directory through production
loading, task creation/binding, encoding, masks and action conversion without
Python registration. Test both directly supplied core-loaded data and ID/directory
loading, with meaningful dimensions, roster and reinforcement changes. Cover
changed ownership, stats/bounds,
objectives, arrivals, terrain/roads and horizon; reject numeric overflow,
nonfinite inputs, orphan/duplicate units and unsupported objective rules clearly.
Demonstrate before/after Crossroads behavioral parity. These tests establish the
data-driven decision boundary, not playable environments, checkpoint compatibility
across spaces or completion of 08's remaining gates.

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

Deliver AC-001–AC-006, a repeatable bounded inspection command, a concise input/mask audit and seed/action traces covering arrival and objective completion. Only after implementation and verified evidence update the schedule and `PPO.md`; this specification alone does not complete 08.

## 11. Related Specifications / Further Reading

[07 — Playable slice](07-trained-9x9-human-visible-slice.md) · [06 — Multi-unit contract](06-multi-unit-design.md) · [API integration boundary](spec-architecture-game-agent-integration-boundary.md) · [Active schedule](playable-player-schedule.md) · [PPO status](../../battle_agent_rl/PPO.md)

Core contract references: [Crossroads scenario](../../battle_hexes_core/src/battle_hexes_core/scenarios/d_day_crossroads.json), [turn transitions](../../battle_hexes_core/src/battle_hexes_core/game/game.py), [reinforcement deployment](../../battle_hexes_core/src/battle_hexes_core/game/reinforcements_deployer.py), [scoring](../../battle_hexes_core/src/battle_hexes_core/scoring/objective_scorer.py), [completion](../../battle_hexes_core/src/battle_hexes_core/scoring/game_status_evaluator.py).

## Open Questions

No questions.
