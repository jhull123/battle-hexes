---
title: "PPO Agent 07: Trained 9×9 Human-Visible Slice"
date_created: 2026-10-16
tags: [design, ppo, reinforcement-learning, api, web]
---

# Introduction

Deliver one experimental, human-playable 9×9 PPO opponent using a **trained, saved, reloaded** multi-unit policy. This increment proves the live core/API/UI path; it does not establish playing strength or produce a Crossroads policy.

## 1. Purpose & Scope

For implementers and reviewers of [schedule 2, increment 07](playable-player-schedule.md), extend the [06 prototype](06-multi-unit-design.md) with bounded masked training, a validated frozen artifact, and a backend-connected human game. Support exactly the fixed two-versus-two setup, PPO as the **first** side (`Learner`), human as the second (`Opponent`). Keep existing 5×5 training/inference and ordinary batch-player games working. Crossroads, arbitrary rosters/boards, self-play, checkpoint selection campaigns, and a strength threshold are out of scope.

## 2. Definitions

- **PPO:** Proximal Policy Optimization, implemented by SB3-Contrib `MaskablePPO` with `MultiInputPolicy`.
- **Slot/order:** A persistent unit ID and its one destination choice per friendly movement phase. One PPO request issues at most one order.
- **Cycle:** One PPO turn followed by one human turn, unless core completes earlier. Core turn number identifies the current cycle.
- **Mask:** A 162-element boolean vector; `True` means that the slot/destination is currently legal under core movement rules.
- **Checkpoint identity:** A manifest-listed artifact name plus its SHA-256 digest and policy contract, bound to a game at creation.
- **Cutoff:** An external training/evaluation stopping bound while core remains `in_progress`; not a game result.
- **Completed result:** Core `GameStatus.state == "completed"`, by elimination or the declared turn limit, including a possible score-tied draw.

## 3. Requirements, Constraints & Guidelines

- **REQ-001 — Playable contract:** Introduce `battle-hexes-9x9-2slot-unit-destination-live-turnlimit50-v2` for scenario `ppo_9x9_experimental`, version `1`. Keep 06's `...live-v1` prototype unchanged and reject its checkpoints for playable games. The only deliberate rules change from 06 is a **50-cycle core turn limit** so a human game can finish without exceeding the policy's horizon; an explicitly neutral open-terrain display, if needed by the scenario loader/UI, must have movement cost 1, defensive-fire modifier 1 and combat odds shift 0. Train, evaluate and serve **v2** on the same core-loaded scenario, including its turn-limit scoring. Do not relabel v1 weights or reinterpret its `remaining_cycles` input.
- **REQ-002 — Policy input and turns:** Retain 06's four stable slots, Dict observation shapes/dtypes, `Discrete(162)` mapping (`slot * 81 + row * 9 + column`), core-derived mask and path validation, hold action, live defensive fire, post-order retreat feedback, and single combat phase per side. For v2, `remaining_cycles` is `[51 - game.turn_number]` (50 at reset, 1 on turn 50); never derive it from a smaller smoke/evaluation cutoff. An eliminated/ordered slot cannot be selected again. Once no living PPO slot is pending, use core's movement-phase closure, one combat resolution if applicable, and end-turn transition; stop at core completion, including completion during movement. A human turn uses its existing movement/combat workflow and returns to PPO only after core ends that turn. Both sides use the same scenario rules and core resolution; neither route nor schema computes victory.
- **REQ-003 — Training:** Provide a bounded CPU masked-PPO command with seed, positive requested timesteps, rollout size (>1), batch size (>1 and no greater than rollout size), and a new run directory. Use native current-state masks during **both** rollout and deterministic prediction. Preserve 06's sorted-joint-index seeded random opponent for training/evaluation only; human input replaces it in playable games. Record actual timesteps, completed optimizer updates, outcomes and cutoff counts separately, and evidence that at least one tensor changes. Keep training dependencies out of core and the lightweight 06 inspector.
- **REQ-004 — Artifact:** Save a model after a completed update, with a versioned JSON manifest recording scenario ID/version or immutable scenario fingerprint, v2 contract, 50-turn horizon, action/observation spaces, roster/seat, training seed/configuration and actual timesteps, CPU/software versions, relative model path and SHA-256 digest. Do not overwrite an existing run. Load on CPU in a fresh process; verify the manifest, file digest, versions, spaces, scenario/rules and slot mapping **before** prediction. Reject unknown paths, v1/5×5 archives, corrupt or incompatible models, and missing serving artifacts with clear errors; never silently use initialized/random weights. The serving artifact is an administrator-configured, manifest-listed checkpoint, not a client-provided filesystem path; fail unavailable at selection/creation rather than mid-turn.
- **REQ-005 — Frozen live inference:** Encode observations/masks and convert actions to core plans using shared v2 training/inference code; choose once with `deterministic=True` and the current mask. Validate action legality and path before applying one plan through core; never substitute hold after a bad prediction. Predict again only after that move and its fire/retreat have been resolved and persisted. Do not train, assign rewards or mutate model weights in callbacks or HTTP commands. Refuse a wrong side, phase, scenario, roster, horizon, checkpoint or empty active mask rather than running a batch `Player.movement()` that cannot observe fire between orders.
- **REQ-006 — Durable turns:** Persist the checkpoint identity, PPO pending slot IDs and shared game RNG continuation with the authoritative game state. Prune a pending slot if its unit dies; never restore it by recomputing from remaining movement points. Validate these fields against the scenario, current player/phase, living units and the **game-bound** manifest entry on hydration; if its artifact is no longer available, fail rather than substituting the server's new default. Do not serialize a model, executable object or pickle into game state; use validated JSON data for RNG continuation. Every successful PPO order atomically commits its movement, fire, pending changes and RNG state with the next game version under the existing expected-version/idempotency protocol. The final PPO order also finishes that side's movement, resolves its one combat phase and advances through core when active. Existing human commands for this scenario must use the same persisted RNG continuation for fire and combat; retries/reloads must not resample rolls or issue another order. On completion persist core's terminal phase/status consistently with the existing codec. Make the persisted extension optional for older/non-PPO snapshots, with an explicit state-schema migration if required; do not alter non-PPO turn behavior.
- **REQ-007 — API boundary:** Advertise a separately named `ppo-9x9-experimental` player type, restricted to `playerTypes: ["ppo-9x9-experimental", "human"]` on `ppo_9x9_experimental`. Reject unsupported combinations at creation with a client error. Add one PPO-only atomic order command (section 4); do not expose client-selected PPO actions, generic `/movement` batching, or manual end-movement/combat/turn commands on the PPO side. Preserve ordinary `/move`, `/end-movement`, `/combat` and `/end-turn` for the human side with authoritative ownership/phase checks. Keep routes thin, core rules in core, and API schemas limited to validation/serialization of already-computed results.
- **REQ-008 — Human-visible result:** Offer the experimental scenario and PPO choice only in the supported seats; label them **Experimental — trained 9×9 PPO (no skill claim)**. The backend-connected UI issues and animates each PPO order separately, shows defensive fire/retreat before requesting the next order, shows combat and handoff once per side, and resumes from `GET /games/{id}` after reload using authoritative pending/phase and checkpoint identity. Render core-completed win/loss/draw and reason using existing game-over behavior. Never display a training/evaluation cutoff as a completed human game. Preserve ordinary CPU/batch player UI behavior.
- **CON-001:** The human game has no external 50-cycle cutoff: on the last completed human turn, core's 50-turn rule decides the result. If an evaluation intentionally stops earlier, report `cutoff` with core still `in_progress`; completion on the bound takes precedence.
- **CON-002:** Split scenario/policy conversion, trainer, artifact validation, live turn orchestration, API command adaptation, persistence and UI rendering by responsibility. Reuse the live resolution sequence and current-state encoder rather than duplicating training/inference implementations. If implementation must depart from this numbered contract, ask the user before changing it.

## 4. Interfaces & Data Contracts

### Fixed scenario and policy

Scenario JSON is registered under `battle_hexes_core/src/battle_hexes_core/scenarios/`: 9×9; 50-turn core limit; no objectives, roads, reinforcements or stacking cap; default fire base `0.25`, minimum `0`, maximum `1`; two infantry per side, attack/defense/move `2/2/2`, fire modifier `1`. Player order and unit insertion order: `Learner`/`learner-0` at `(3,2)`, `learner-1` at `(5,2)`; `Opponent`/`opponent-0` at `(3,6)`, `opponent-1` at `(5,6)`. A neutral visual terrain must not change these rules. Define the core-loader scenario once; training must not maintain a conflicting hand-built scenario.

The 06 observation fields remain `positions` (`int8[4,81]`), `present`, `alive`, `movement_remaining`, `defensive_fire_ready`, `fire_eligible_last_turn`, `forced_retreat`, `fire_spent` (each `int8[4]`), `pending` (`int8[2]`), and `remaining_cycles` (`int32[1]`, range 0–50). The separate mask is `bool[162]`; missing/dead slots retain the 06 padding/identity semantics. The first holds are actions `29` and `128`. A last-unit death completes via core even if the other slot was pending.

### Training and evaluation entry points

Provide documented invocations such as `python -m battle_agent_rl.ppo.multi_unit_train --seed 0 --total-timesteps 64 --n-steps 16 --batch-size 8 --run-dir /tmp/opencode/ppo-07-smoke` and `python -m battle_agent_rl.ppo.multi_unit_evaluate --run-dir /tmp/opencode/ppo-07-smoke --seeds 1000:1020`. The exact command spelling may follow existing CLI conventions, but must expose the stated arguments, bounded replay, manifest path and outcome records. Predeclare and record ordered evaluation seeds `1000..1019` for the demonstration; reject overlap with recorded training episode seeds. Evaluation reloads the saved artifact, runs one game per seed with core completion or a declared external cycle cap, and records `{gameSeed, outcome: win|loss|draw|cutoff, learnerDecisions, coreStatus}`. Report four counts over all seeds; no win-rate gate or held-out strength claim is required. For an early cap, still supply the true 50-turn `remaining_cycles` to the model.

### API and persisted state

- `POST /games` accepts `{ "scenarioId": "ppo_9x9_experimental", "playerTypes": ["ppo-9x9-experimental", "human"] }` only when the configured validated artifact is available.
- `POST /games/{game_id}/ppo/order` has no client-selected action and requires the existing `Idempotency-Key` and `Expected-Game-Version` headers. It commits **at most one** PPO order; response includes the resulting `gameVersion`, `game` projection, one `plan` (`unitId` and path), this command's `defensiveFireEvents`, this command's combat events if it closed movement, and authoritative `ppoTurn` (`pendingUnitIds`, `checkpointDigest`, `contract`). Use HTTP API camelCase. An early core completion may omit further combat; `pendingUnitIds` is empty when no next PPO decision exists. An incompatible state, non-PPO phase, stale expected version or missing game-bound artifact fails without committing state; an exact retry returns the original receipt.
- `GET /games/{game_id}` includes the optional `ppoTurn` metadata whenever this game uses PPO (pending list empty off the PPO movement phase), and the existing game status/phase. The authoritative persisted extension stores validated checkpoint identity, two-slot pending state and RNG continuation; it is preserved across process restart and optimistic-concurrency retries. No existing client must require `ppoTurn` on other games.

## 5. Acceptance Criteria

- **AC-001:** Given the v2 scenario and bounded seed-0 run, when training ends, then masked rollout actions are legal, at least one optimizer update changes parameters, and a versioned manifest and model exist. Given its reloaded checkpoint, deterministic masked actions match pre-save actions on matching live decision states without weight changes.
- **AC-002:** Given v1/5×5, wrong scenario/side/turn limit, missing/damaged artifact or changed software/spaces, when a game is created or a model loaded, then the attempt is rejected before a PPO order; existing 06 inspection and 5×5 tests still pass.
- **AC-003:** Given two PPO units pending, when the first order triggers defensive fire and retreat/removal, then the next response/observation/mask reflect the resolved state, the first unit is not offered again, and combat has not run. On the final order, combat runs at most once and core hands off to the human unless completed.
- **AC-004:** Given a pending second order, when the browser or server restarts, then GET and the next successful command use the same checkpoint digest, pending slot, movement/fire state and RNG continuation. Replaying a key produces the same response without another order; stale versions, wrong phase and incompatible snapshots fail without mutation.
- **AC-005:** Given a human acting second, when both sides complete turns, then existing human commands still work, PPO decisions are one-at-a-time, and on elimination or the end of core turn 50 the backend and UI show the same completed winner/draw and reason. An evaluation cutoff with core `in_progress` is not shown as a human-game result.
- **AC-006:** Given declared seeds `1000..1019`, when evaluating the saved model, then per-seed records and win/loss/draw/cutoff totals reconcile and rerunning with the same artifact, seed/RNG protocol and runtime reproduces records. The report makes no strength claim from the smoke run.
- **AC-007:** Given a non-PPO game, when its existing API and UI movement/combat flow runs, then the batch-player contract, persistence and responses remain usable.

## 6. Test Automation Strategy

- **Unit (`pytest`, `battle_agent_rl/tests/ppo`):** Short real masked training; changed weights, legal mask on rollout/prediction, fresh-process reload, digest/version/space/scenario rejection, stable slots and post-fire parity. Compare matched core decision states from trainer and live service; never infer identical trajectories from seed alone when the human differs from the random training opponent.
- **API/persistence (`pytest`):** Real core command paths, supported/unsupported seat creation, two-order mid-turn hydration (in-memory and configured durable repository tests), optimistic concurrency and receipt replay, persisted RNG continuity, terminal codec validation, fire/combat event visibility, and regression coverage for random/Q-learning batch players. Test outcomes/phase transitions, not exact log strings.
- **Web (existing JS tests):** Supported-seat picker, per-order animation and event display, reload/resume with pending order, terminal display and unchanged ordinary CPU play. Run `npm run test-and-build` for web changes.
- **Backend-connected acceptance:** Run the actual API with a configured trained artifact and persistent repository; record a reproducible human-versus-PPO playthrough including live fire/retreat, mid-turn reload and a core-completed result. A CLI trace, mock service, initialized model or cutoff does **not** pass this gate. Run `./server-side-checks.sh`; keep the smoke run bounded and record separate evaluation artifacts, not a skill-threshold CI test.

## 7. Rationale & Context

The 06 policy sees remaining *cycles* and has no core time limit. A human game allowed to continue past its 50-cycle horizon would change the input semantics or leave the observation space. A separate v2 scenario with a matching core turn limit solves this without pretending a training truncation is a draw or silently reusing v1 weights. Per-order API commands are necessary because `Player.movement()` chooses an entire batch before seeing defensive fire; versioned receipts and persisted pending/RNG state allow the UI to reload between choices. A fixed smoke run tests connectivity and artifact integrity, not generalization; Crossroads requires its own contract and training in 08–12.

## 8. Dependencies & External Integrations

- **EXT-001:** Core scenario loader, movement plans/reachability, defensive fire, combat, phase transitions and game-status evaluation; core remains independent of PPO libraries.
- **PLT-001:** Existing CPU Python/Gymnasium/NumPy/PyTorch/SB3-Contrib stack for training and prediction, plus existing FastAPI and p5.js application contracts.
- **DAT-001:** 06 slot/action/observation design and 04 artifact-validation conventions; a newly trained **v2** artifact is required for serving.
- **INF-001:** Existing API game repository, codec, expected-version and idempotency receipt mechanism, and a deployment-accessible configured checkpoint; browser never reads model files.

## 9. Examples & Edge Cases

- At turn 1 with both PPO slots pending, `remaining_cycles=[50]`; ordering slot 1 to hold at `(5,2)` uses `128`, leaves slot 0 pending, and does **not** start combat. At the next prediction the mask contains only slot 0's block, based on the post-order board/fire state.
- If defensive fire eliminates the first mover, its order remains spent. If it eliminates the last opposing unit, core completes immediately: do not predict, execute combat or hand off afterward.
- A game still active after PPO's turn-50 orders remains active until the second (human) side finishes, unless core completes sooner. Core, not an external cutoff, decides the turn-50 result. A smoke evaluation deliberately stopped after turn 3 instead records `cutoff`, core `in_progress`.
- After a committed first order, retrying its idempotency key returns that same result; a **new** key with the old expected version conflicts. A fresh request after reload can order only a still-pending unit and must use the game-bound digest, not the server's newly configured default artifact.

## 10. Validation Criteria

Deliver the v2 scenario/contract, bounded training and evaluation invocations with artifacts and honest counts, validated frozen inference, persistent one-order commands, and the backend-connected completed/reloaded UI trace required by AC-001–AC-007. Document artifact configuration and a repeatable local play procedure. Only after implementation **and** verified evidence, mark 07 done in [schedule 2](playable-player-schedule.md) with delivered work/evidence and update [`PPO.md`](../../battle_agent_rl/PPO.md). Creating this spec alone does not complete 07.

## 11. Related Specifications / Further Reading

[06 — Multi-unit design](06-multi-unit-design.md) · [04 — Checkpoints](04-evaluation-and-checkpoints.md) · [05 — Core inference](05-inference-player.md) · [Active schedule](playable-player-schedule.md) · [PPO vision](../../battle_agent_rl/PPO.md)

## Open Questions

No questions.
