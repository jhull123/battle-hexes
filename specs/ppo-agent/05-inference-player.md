---
title: "PPO Agent 05: Inference Player in Core Games"
date_created: 2026-10-13
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Run a frozen, compatible masked-PPO checkpoint as a normal core `Player` in a local game. The player chooses a destination; core alone applies the resulting movement plan, defensive fire, combat, turn handoff, and game outcome.

## 1. Purpose & Scope

This specification is for implementers and reviewers of increment 05 of the [PPO schedule](implementation-schedule.md). Implement `PPOPlayer` under `battle_agent_rl.ppo` for the existing fixed 5×5, one-learner-unit versus one-seeded-random-opponent task. Provide a bounded local core-game demonstration and tests comparing its decisions with deterministic checkpoint evaluation on matching decision states. Preserve the policy-input contract and artifact validation from increments 01–04. Training, reward bookkeeping, policy updates, multi-unit or variable-board support, API/UI integration, and a claim of playing strength are out of scope.

## 2. Definitions

- **PPO:** Proximal Policy Optimization; here, the saved SB3-Contrib `MaskablePPO` policy.
- **Decision:** One call to the learner's `movement()` for one learner turn, followed by core resolution of that turn and, if still active, the opponent turn. One decision consumes one unit of the checkpoint's `step_limit` budget.
- **Mask:** Row-major, 25-element boolean vector of legal destinations; `True` means legal, including the learner's current cell (hold).
- **Core-compatible player:** A subclass of `battle_hexes_core.game.player.Player` whose `movement()` returns a list of `UnitMovementPlan` objects. It does not advance the game itself.
- **Cutoff:** Local demonstration stops after the configured number of learner decisions while core status remains `in_progress`; this is not a core draw or loss.
- **Matching decision state:** Same board occupancy, defensive-fire readiness, learner-to-move state, and remaining learner-decision budget under the fixed policy-input contract. Matching a board alone is insufficient.

## 3. Requirements, Constraints & Guidelines

- **REQ-001:** Expose `PPOPlayer` under `battle_agent_rl.ppo`, with a documented way to load it from a run directory and a manifest-listed checkpoint. Default to the manifest's frozen `selected` entry; if no selection exists, require an explicit entry. Use `read_manifest` and `load_checkpoint` (or their shared validated path): verify contract, software versions, archive digest, observation/action spaces, and manifest `step_limit` *before* using the model. Reject unknown entries, incompatible/corrupt artifacts, or an attempted different decision budget with an actionable error. Load on CPU; never train or mutate weights in player callbacks.
- **REQ-002:** Since `Game` is constructed with its players, permit binding the player to that specific game after construction and before its first decision. At binding, validate the fixed initial scenario in section 4; before every prediction, require that it is that game's current player's turn, core status is `in_progress`, and exactly one living learner unit and one living opponent unit remain. Reject unsupported board, unit, terrain, rules/settings, player-order, or opponent configurations instead of silently applying this fixed policy to another scenario. No general-purpose scenario adapter is required.
- **REQ-003:** Share one source of truth for policy observation, legal mask, and destination-to-core-path conversion between training and inference. Refactor the existing `policy_observation`, `policy_action_mask`, and `PPOTrainingEnvironment._set_learning_plan` boundaries as needed so both paths derive the *current* core state and use core reachability/pathfinding. Do not instantiate or step `PPOTrainingEnvironment` to make an inference decision, fabricate a stale `Transition`, cache an earlier mask, or reimplement movement rules. Keep the 03 observation fields, dtypes, row-major ordering, mask semantics, and action index mapping unchanged.
- **REQ-004:** At each valid learner turn, form `remaining_steps = manifest.step_limit - decisions_already_issued` (initially `step_limit`). Call `model.predict(observation, action_masks=current_mask, deterministic=True)` once; require a scalar integer in `[0, 24]` marked `True` in that same mask. Convert index `i` to `(i // 5, i % 5)`, use core `shortest_path` from the learner's *current* position (including the hold path), and return a one-element `list[UnitMovementPlan]`. Fail clearly before returning any plan if no legal action or valid path exists; do not substitute hold after an invalid model prediction. Only a successfully issued plan consumes a decision. After returning a plan, reject any further `movement()` call in that same learner turn before prediction, even if core has applied the plan but has not advanced the turn; the rejected call consumes no decision. Do not predict on a completed game or an exhausted budget.
- **REQ-005:** Keep `movement()` limited to selecting and returning plans; `movement_cb()`, `combat_results()`, and `end_game_cb()` must not assign rewards, train, classify cutoffs, or advance turns. Provide a bounded local driver or documented example which constructs an ordinary core `Game` with the supported units, players, board and defensive-fire settings; applies each player's returned plans via core, resolves combat through core with the seeded game RNG, refreshes core status after combat, advances via core if still active, and stops after a completed core result or after the opponent turn following the final learner decision. Share the existing environment's turn-resolution sequence where practical rather than maintaining two competing sequences. Report completed status versus cutoff separately. Do not equate `GamePlayer.play(max_turns=...)` with `step_limit`: it counts *both* players' turns, and its default combat RNG is not the training environment's seeded RNG.
- **CON-001:** Keep all PPO and dependency-heavy inference code in `battle_agent_rl.ppo`; core `Player` and game rules remain independent of Gymnasium/SB3. Importing or using the random baseline must not require a trained artifact.
- **CON-002:** Local parity is about deterministic *choices given matching decision states*, not identical trajectories under differing opponent/game RNG protocols. For full seeded episode parity, reproduce the environment's initial setup, single shared `random.Random(seed)` for opponent and core random effects, turn order, and cutoff timing. Never claim that identical seeds alone imply identical trajectories with a differently configured driver.
- **CON-003:** Separate artifact loading, state encoding/action-plan conversion, and core-game orchestration into cohesive components; do not copy the evaluation loop into player callbacks. Proposed deviations from numbered specifications require a user decision before implementation.

## 4. Interfaces & Data Contracts

Document a public construction/binding API (for example, `PPOPlayer.from_checkpoint(name, factions, run_dir, checkpoint=None)` followed by `player.bind_game(game)`). `PPOPlayer` must have `type=PlayerType.CPU`, own the passed faction, and implement `movement() -> list[UnitMovementPlan]` and the required no-op `combat_results()` callback. A bind must reject another game after decisions have begun; rebinding the same game must not reset the decision count or same-turn guard. The selected-entry default and explicit-entry behavior must be documented; neither accepts an arbitrary `.zip` outside the validated manifest.

The prediction input is the 03 `Dict` observation: `occupancy` (`int8[25]`: learner `1`, opponent `-1`, empty `0`), `defensive_fire_ready` (`int8[25]`: 0/1 from `unit.public_defensive_fire_status(learner)`), and `remaining_steps` (`int32[1]`). The mask is `bool[25]` from current core reachability. The current learner cell is the hold action. Use the same shared encoding in `MaskedBattleHexesEnv` and direct player inference, including after retreat or defensive fire; inference does not receive a Gym environment, reward, or episode `info`.

The supported initial game has a 5×5 open board, one learner infantry unit at `(2, 0)` and one opponent infantry unit at `(2, 4)`, each with attack, defense, and movement values `2`; the learner moves first, against `SeededRandomPlayer`, with defensive-fire base probability `0.25` and no other scenario rules or terrain modifiers. Bind to this game before any moves; positions may subsequently change through core movement, combat and retreat. Use the fixed scenario's seeded RNG for the opponent, defensive fire and combat in the parity driver.

The demonstration's `step_limit` is read from the checkpoint manifest, not inferred from `Game.turn_number` or `Game.turn_limit`. For a decision at count `k` (starting at zero), predict with `remaining_steps = step_limit - k`; after issuing decision `step_limit`, finish core resolution of the learner and (if active) opponent turns before reporting a cutoff. A core completion on either turn takes precedence over cutoff. The same model prediction helper may be used by checkpoint inspection/evaluation where practical; all prediction paths must pass the current mask.

## 5. Acceptance Criteria

- **AC-001:** Given a valid frozen checkpoint and supported game, when `PPOPlayer.movement()` is called on multiple reachable learner decision states, then its selected indexes equal deterministic masked evaluation on matching observations/masks, its plans target legal core destinations, and model parameters do not change.
- **AC-002:** Given a retreat or defensive-fire change, when the learner next acts, then observation, mask, hold position, and path reflect the current post-resolution core board and readiness rather than the prior turn.
- **AC-003:** Given a bad checkpoint, mismatched step limit/contract, unsupported scenario, opponent turn, terminal game, or exhausted budget, when construction/binding or prediction is attempted, then it fails clearly rather than issuing an unmasked or illegal plan. A second `movement()` call in the same learner turn must fail before prediction without decrementing the remaining budget, including after a same-game rebind.
- **AC-004:** Given the same frozen checkpoint, game seed and fixed configuration, when a local core game is replayed, then action trace, completed/cutoff classification, and core game outcome repeat; movement, defensive fire, combat and turn handoff occur through core. If the last decision completes the game, report completion, not cutoff.
- **AC-005:** Given a fixed seed and equivalent RNG/turn protocol, when comparing a bounded core-game trace with the 04 evaluation path, then decision inputs and chosen actions match at each corresponding learner turn. The comparison checks policy integration, not win-rate improvement.

## 6. Test Automation Strategy

Use focused `pytest` tests under `battle_agent_rl/tests/ppo` with a small real checkpoint fixture or bounded saved model. Cover loading the selected and explicit manifest entries, rejection of invalid artifacts/configurations, current-state observation and mask equality with the Gym/training adapter, legal reachable plans including hold and post-retreat positions, invalid model action/no-mutation behavior, decision-budget boundaries, and repeated calls on the same, wrong, or ended turn. For a same-turn repeat, assert no second prediction and no budget consumption, both before and after applying the first plan and after rebinding the same game. Run seeded local core games and compare per-decision observation, mask, action, and ending with the evaluation path using the same checkpoint; include defensive fire/combat and completion-on-limit cases. Check model weights remain unchanged. Keep tests short; no skill threshold, retraining requirement, API request, or browser test. Run `./server-side-checks.sh` after implementation.

## 7. Rationale & Context

The existing Gym adapter accepts `Transition` objects, while a core `Player` sees a live `Game`; a shared core-state encoder is necessary to prevent training/inference drift. `remaining_steps` is a learned input, so removing it or deriving it from player-turn count changes the policy contract. Core's `GamePlayer` can run ordinary players, but its turn bound and RNG behavior cannot establish seeded parity with the fixed PPO environment without additional control. Increment 04's held-out policy did not beat center-then-hold; increment 05 verifies integration, not improved skill.

## 8. Dependencies & External Integrations

- **DAT-001:** Increment 04 manifest, selected entry, validated `.zip` checkpoint, and fixed policy-input contract.
- **EXT-001:** `battle_hexes_core` `Player`, `Game`, board reachability/pathfinding, `UnitMovementPlan`, movement, combat, defensive fire, status and turn APIs.
- **PLT-001:** Existing compatible CPU SB3-Contrib/Gymnasium/NumPy/PyTorch runtime for loading and predicting; no network or UI integration.

## 9. Examples & Edge Cases

- At the first learner decision with `step_limit=50`, `remaining_steps` is `[50]`; after four successfully issued learner plans it is `[46]`, regardless of the number of opponent turns or the core turn number.
- A learner at `(2, 0)` holding chooses index `10`; after a forced retreat, hold means the *new* current cell, not index `10`. Core still resolves combat for a hold plan.
- With `step_limit=1`, a completed core game on the learner or opponent turn is `completed`; if both turns finish with status `in_progress`, the local driver reports `cutoff` and leaves core status unchanged. There is no second call to `movement()`.
- An all-false mask, an action not marked legal, a missing core path, or a mismatched checkpoint is an error, never an invitation to choose another action silently.

## 10. Validation Criteria

Provide a copyable local command or example that loads a manifest-selected frozen checkpoint and runs bounded seeded core games, plus reproducible traces demonstrating action/observation/mask parity with checkpoint evaluation on corresponding decision states. Verify artifact/scenario rejection, legal plans, callbacks without learning, core combat/turn execution, and correct completion versus cutoff using AC-001 through AC-005. Passing tests proves integration only. After implementation and verified evidence, update the schedule and `battle_agent_rl/PPO.md`; writing this spec alone does not mark 05 done.

## 11. Related Specifications / Further Reading

- [01 — Minimal training environment](01-training-environment.md)
- [02 — Rollout inspection and observation audit](02-rollout-inspection.md)
- [03 — First masked PPO training loop](03-masked-ppo-training.md)
- [04 — Evaluation, visualization, and checkpoints](04-evaluation-and-checkpoints.md)
- [Implementation schedule](implementation-schedule.md)
- [PPO agent vision](../../battle_agent_rl/PPO.md)

## Open Questions

No questions.
