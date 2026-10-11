---
title: "PPO Agent 04: Evaluation, Visualization, and Checkpoints"
date_created: 2026-10-11
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Measure whether the fixed Battle Hexes masked-PPO policy improves over reproducible baselines, display progress across training, and retain a reloadable selected policy. Evaluation must separate checkpoint selection from final reporting.

## 1. Purpose & Scope

This specification covers local training-time snapshots, evaluation, reporting, and tests in `battle_agent_rl.ppo`. It builds on the [03 trainer](03-masked-ppo-training.md), the audited [02 policy inputs](02-rollout-inspection.md), and the fixed [01 environment](01-training-environment.md). It is for implementers and reviewers of increment 04. The scenario remains 5×5 with one learner unit against the existing seeded random opponent. A core `PPOPlayer`, API/UI integration, new game rules, reward shaping, and a larger scenario are outside this increment.

## 2. Definitions

- **Checkpoint:** A saved SB3-Contrib `MaskablePPO` model after a completed training update, with metadata identifying its policy contract and training position.
- **Game seed:** Integer passed to the environment reset; it controls opponent choices and game/combat randomness. Distinct policies receive fresh environments reset to the same game seed for paired comparison; their RNG streams may diverge after different actions.
- **Policy-local seed:** Independent seed used only for the random learner's action sampling.
- **Hold baseline:** Learner chooses its current cell at every decision; the opponent still acts, and combat and defensive fire still resolve.
- **Cutoff:** Step-limit truncation while core status is `in_progress`, distinct from a core draw.
- **Validation set:** Games used repeatedly to compare candidate checkpoints and select one.
- **Held-out set:** Disjoint games used to report the performance of the selected frozen checkpoint only.
- **Score:** `(wins + 0.5 * draws) / games`; losses and cutoffs contribute zero. Score complements, rather than replaces, the separately reported outcome rates.

## 3. Requirements, Constraints & Guidelines

- **REQ-001:** Extend the 03 single-CPU-environment training workflow to save the model after specified completed PPO updates and at the final update. Use one continuous `learn` run, so checkpointing/evaluation does not reset the optimizer, timestep counter, or episode-seed sequence. Record actual collected timesteps (which can exceed the requested total), training seed and configuration, step limit, fixed scenario/policy-input contract identifier, software versions, and checkpoint path. Use `MaskablePPO.save`/`MaskablePPO.load(..., device="cpu")`; retain both the selected checkpoint and the evaluated candidate snapshots in a named local run directory without silently overwriting a prior run.
- **REQ-002:** Validate metadata and the model's observation/action spaces against the current fixed adapter before evaluation or inspection. Reject missing/corrupt archives, absent or incompatible metadata, and mismatched step limits or policy-input contracts with a clear error. Loading for prediction must not require or restart training. Reuse `policy_observation` and `policy_action_mask`/`action_masks()` from 03 and pass the current mask to deterministic PPO prediction; never predict on an ending's all-false mask.
- **REQ-003:** Provide an explicit mask-aware evaluation path using `sb3_contrib.common.maskable.evaluation.evaluate_policy` (or `MaskableEvalCallback` where appropriate), not ordinary SB3 evaluation. Collect per-episode outcome, learner decision count, return, and seed from `ppo_episode`/environment diagnostics as well as the utility's reward/length results; verify that both views agree. If wrappers/vectorization are used, preserve native masks and terminal episode summaries. Evaluation environments must be independent of the training environment and must not update model parameters. Reuse the 02 audited inspector for optional individual checkpoint traces rather than building a second board renderer.
- **REQ-004:** For each evaluation seed run exactly one bounded episode for each of three learner policies: deterministic masked PPO, uniformly random legal action, and hold. All three face the same existing seeded random opponent in fresh environments at the same game seed and step limit. Sample random learner actions from sorted legal indexes with a policy-local `random.Random(game_seed)`, separate from opponent/game RNG; hold is always selected via the current legal mask. Reject illegal actions and episodes that do not end by completion or cutoff. No-op never suppresses opponent turns, defensive fire, or combat.
- **REQ-005:** Fix disjoint seed sets and a selection rule before running comparisons. Default validation game seeds are `1_000_000..1_000_199` and held-out seeds are `2_000_000..2_000_199` (200 each). Training seeds are the actual per-episode seeds recorded by the trainer, not simply its initial `--seed`; fail the experiment if either evaluation set overlaps any training episode seed or each other. Permit explicit alternate sets only when the complete ordered seed lists, their role, and the selection rule are recorded before use; do not change them after inspecting results. Re-evaluate all candidate checkpoints on the same validation set. Choose the highest validation score, breaking ties by lower actual training timestep, then by checkpoint path. Never use held-out results for checkpoint selection, hyperparameter tuning, or a second selection pass.
- **REQ-006:** Produce a machine-readable per-episode record and a readable table (a chart is optional) for each checkpoint and policy on validation seeds, ordered by actual collected training timesteps. Report game count, win/loss/draw/cutoff counts and rates, mean and median learner decisions, mean return, score, and paired score differences against random and hold. Report the selection rule and selected checkpoint. Training episode outcomes and update losses may be shown as context but are not the comparison metric. Produce the same table for the frozen selected checkpoint and both baselines on held-out seeds, with uncertainty intervals and an explicit conclusion: improvement supported, inconclusive, or worse. Contrast validation and held-out estimates for the selected checkpoint with their sampling uncertainty; investigate large discrepancies as possible overfitting rather than requiring identical results from independent seeds. Preserve per-seed results so every aggregate can be recalculated.
- **REQ-007:** For the final comparison, compute a two-sided 95% percentile interval of each paired score difference by resampling whole game seeds with replacement 10,000 times. For each seed, pair the selected policy's game score (`1` win, `0.5` draw, `0` loss/cutoff) with the baseline's game score; average differences in each resample. Use an independent `random.Random(0)` bootstrap generator, draw `games` paired seed records per resample, and sort the 10,000 resulting means; the endpoints are zero-based indexes `249` and `9749`. Report the observed point difference and interval for each baseline. Claim held-out improvement only if the lower endpoint is greater than zero against **both** baselines. Otherwise state that improvement is unproven (or worse if both upper endpoints are below zero); do not demand a win as the condition for implementing this increment. State that a cutoff is neither a loss in core nor a draw even though its score contribution is zero.
- **CON-001:** Core owns movement, combat, and game outcomes. Preserve 01 rewards, 02 observation/mask meanings, 03 training seeding, and the random/hold inspector. Do not treat training losses or an in-sample trajectory as evidence of skill.
- **CON-002:** Keep artifact I/O, evaluation/orchestration, metric aggregation, and CLI/report presentation in cohesive components rather than one service module. The checkpoint is an input to increment 05, not an implementation of its core `Player` interface. Resolve any proposed deviation from this numbered specification with the user before implementation.

## 4. Interfaces & Data Contracts

Provide documented commands from the repository root to (a) train with a total-timestep bound and checkpoint interval measured in completed updates, (b) select on validation and evaluate the frozen selection on held-out seeds, and (c) reload and evaluate an existing checkpoint without retraining. Extend the existing `battle_agent_rl.ppo.train` entry point or use focused `battle_agent_rl.ppo` modules; document exact CLI flags, output paths, and an example command for each operation. Invalid intervals, seed overlaps, incompatible artifacts, and incomplete episode records must fail nonzero rather than producing a partial success report.

Each run directory contains model `.zip` files, a metadata/manifest file (JSON), and per-episode evaluation records in JSON or CSV plus a human-readable table. Required record fields are `split`, `checkpoint`, `training_timesteps`, `policy` (`ppo`, `random`, `hold`), `game_seed`, `outcome` (`win`, `loss`, `draw`, `cutoff`), `length` (learner decisions), and `return` (sum of environment rewards). The manifest records training and evaluation configuration, actual training episode seeds, ordered validation and held-out seeds, selection rule, selected artifact, policy-input contract identifier, Python/NumPy/PyTorch/Gymnasium/SB3/SB3-Contrib versions, CPU setting, and interval method. Do not serialize core objects or RNG internals in these records. Rates have denominator `games`, including cutoffs; core draws exclude cutoffs. All reported lengths/returns are from finished or truncated episodes, not SB3 rollout fragments.

`MaskedBattleHexesEnv.reset(seed=s)` starts game seed `s`; a fresh environment is reset explicitly for every evaluation game so its automatic sequential-reset behavior cannot silently alter the evaluation seed set. `ppo_episode` already supplies outcome, length, return, and game seed at the ending. Record training episode seeds at reset, including an unfinished episode at the end of a rollout, for overlap checks. For checkpoint comparison, evaluate saved/reloaded artifacts, not only the in-memory model; a selected artifact's digest or equivalent immutable identity must appear in both selection and final reports.

## 5. Acceptance Criteria

- **AC-001:** Given an updated model saved after a completed update, when loaded in a fresh process with the same software and policy-input configuration, then its deterministic masked choices across multiple reachable decision states match the pre-save model, each action is legal, and the selected checkpoint can be evaluated without training.
- **AC-002:** Given the same checkpoint, ordered game seeds, step limit, baseline seed protocol, and CPU/software configuration, when evaluation is repeated, then per-seed outcomes, lengths, returns, actions (where recorded), and aggregate metrics agree; changing to a disjoint seed set produces an independently estimated result rather than a replay claim.
- **AC-003:** Given a validation sweep, when candidate scores tie, then the earlier actual training timestep wins; held-out seeds have not been evaluated for any unselected candidate or used to alter the selection.
- **AC-004:** Given a cutoff, when summarizing games, then it appears only in the cutoff count, contributes zero to score, and retains core `in_progress`; a completed draw on the last allowed decision is a draw, not a cutoff.
- **AC-005:** Given a reported final result, when recomputed from per-seed records, then counts, rates, means/medians, paired differences, confidence intervals, and the supported/inconclusive/worse label follow the specified rules; a short inconclusive run can complete without claiming skill.
- **AC-006:** Given a new run directory and requested update interval, when training finishes, then snapshots appear at completed updates and the final update with distinct actual timesteps, and the report orders their validation metrics as a readable progression.

## 6. Test Automation Strategy

Use focused `pytest` tests under `battle_agent_rl/tests/ppo`: a short real masked-PPO run with at least two checkpoint positions; save/reload deterministic masked decisions; a fresh-process or equivalent independent load/evaluation path; seed separation and selection/tie tests; paired baseline evaluation with legal random and hold moves; outcome accounting for cutoff versus last-step core completion; and metric/bootstrap calculation from small synthetic records with known results. Check repeated evaluation of one frozen checkpoint and matching recorded per-seed results, then sample another non-overlapping seed set and report its uncertainty without requiring identical rates. Test that evaluation does not mutate model weights. Keep automated learning runs bounded and do not require a stochastic training run to pass a skill threshold. Run `./server-side-checks.sh` after implementation; record a separate, larger fixed-protocol validation/held-out experiment as completion evidence rather than making it an everyday CI job.

## 7. Rationale & Context

The 03 smoke trainer proves updates but not playing strength. Equal game seeds control starting conditions and random-opponent/game seeding across policies, while distinct learner choices can consume randomness differently; pairing estimates a difference without claiming identical trajectories. Validation permits repeated checkpoint comparisons; reserving the held-out set prevents selection bias in the final report. Explicit cutoff accounting avoids inflating draws or hiding step-limit failures. A tabulated progression makes regressions visible without adding a visualization dependency.

## 8. Dependencies & External Integrations

- **DAT-001:** The fixed `PPOTrainingEnvironment`, `MaskedBattleHexesEnv`, `ppo_episode` summary, policy encoders, and seeded rollout inspector from increments 01–03.
- **EXT-001:** `battle_hexes_core` for authoritative outcomes and seeded game behavior.
- **PLT-001:** The existing 03 CPU-compatible Gymnasium, NumPy, PyTorch, Stable-Baselines3 and SB3-Contrib installation; use SB3-Contrib's mask-aware evaluation utilities and checkpoint format. No new network service or UI dependency is required.

## 9. Examples & Edge Cases

- If a learner wins on the last allowed decision, record `win`, return `+1`, and `terminated=True`; if play remains active instead, record `cutoff`, return `0`, and `truncated=True`.
- If the learner starts at `(2, 0)`, hold is index `10` (`2 * 5 + 0`). The hold baseline submits `10` while legal; it does not skip `env.step`.
- Two checkpoints with identical validation scores at actual timesteps `512` and `1024` select `512`; both may still appear in the validation progression, but only `512` is evaluated on held-out seeds.
- A hold and a PPO policy on game seed `2_000_000` may follow different opponent/combat rolls after their actions diverge; this does not invalidate the paired-by-seed report.

## 10. Validation Criteria

Provide copyable commands, checkpoint and manifest schema, validation progression, selected-artifact identity, and one held-out report with per-seed records and paired uncertainty. Verify deterministic reload, masked legality, evaluation replay, disjoint seeds, and outcomes against the acceptance criteria. A report of inconclusive skill is an honest completed evaluation if its protocol and artifacts are sound. Only after the increment is implemented and evidence verified, mark 04 done in the schedule with delivered work and evidence and update `battle_agent_rl/PPO.md`; authoring this specification alone does not complete 04.

## 11. Related Specifications / Further Reading

- [01 — Minimal training environment](01-training-environment.md)
- [02 — Rollout inspection and observation audit](02-rollout-inspection.md)
- [03 — First masked PPO training loop](03-masked-ppo-training.md)
- [Implementation schedule](implementation-schedule.md)
- [PPO agent vision](../../battle_agent_rl/PPO.md)
- [SB3-Contrib MaskablePPO evaluation guidance](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html)

## Open Questions

No questions.
