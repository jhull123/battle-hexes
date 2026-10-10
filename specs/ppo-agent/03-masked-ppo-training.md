---
title: "PPO Agent 03: First Masked PPO Training Loop"
date_created: 2026-10-10
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Train on the existing fixed 5×5, one-unit-per-side Battle Hexes task using SB3-Contrib's `MaskablePPO`. This increment establishes a working, inspectable optimizer and a reusable policy-input boundary; it does not establish that the policy is a better player.

## 1. Purpose & Scope

This specification applies to the Gymnasium adapter, local trainer, documentation, and focused tests in `battle_agent_rl.ppo`. It depends on the [01 environment](01-training-environment.md) and the [02 observation audit](02-rollout-inspection.md). Implementers must retain the audited `remaining_steps` feature and the 01 rules, opponent, reward, and cutoff semantics. Checkpoint selection, comparative evaluation, and a core-compatible inference `PPOPlayer` belong to increments 04 and 05.

## 2. Definitions

- **PPO:** Proximal Policy Optimization, the policy-update algorithm supplied by SB3-Contrib.
- **Decision:** One learner destination choice followed by the environment's learner turn and, if still active, opponent turn.
- **Mask:** A length-25 boolean array in row-major order; `True` denotes a currently legal destination. The learner's current cell is the hold action.
- **Episode seed:** Seed for one game's opponent and combat/fire randomness. A training seed also initializes the model's random generators and the adapter's sequence of episode seeds.
- **Cutoff:** An environment step-limit `truncated=True` while core status remains `in_progress`; it is not a draw.

## 3. Requirements, Constraints & Guidelines

- **REQ-001:** Add a Gymnasium `Env` adapter around `PPOTrainingEnvironment`. `reset(seed=None, options=None)` returns `(observation, info)` and `step(action)` returns `(observation, reward, terminated, truncated, info)`. Use the existing environment for game transitions and its existing observation, mask, and action-to-plan conversion; never duplicate legal-move or combat rules. Reject a step after either ending until reset.
- **REQ-002:** Declare fixed `Dict` observation and `Discrete(25)` action spaces, as specified in section 4. Convert the underlying tuple/int data to fresh NumPy arrays of the declared shapes and dtypes. Expose a public `action_masks()` method returning a fresh 25-element boolean NumPy array derived from the current transition, with `True` meaning legal. It must be available at reset and after each non-ending step, including after a vectorized environment auto-reset. An ending transition has an all-false mask; never request another action on that terminal state. Return observations and masks only for the current state, not cached pre-combat state.
- **REQ-003:** Preserve the 01 transition's `info` diagnostics for inspection and add stable, simple episode summary fields at episode end: outcome (`win`, `loss`, `draw`, or `cutoff`), episode length in learner decisions, and episode return. A cutoff must not be counted as a core draw. Keep diagnostics and summaries out of the policy observation. Allow Gymnasium/SB3 to propagate terminal observations and time-limit truncation correctly, including when the last step completes a core game at the limit.
- **REQ-004:** Use SB3-Contrib `MaskablePPO` with `MultiInputPolicy` for the dict observation. Use its own masked rollout collection and PPO updates; do not implement a separate masking sampler, optimizer, or reward shaping. For inference from a trained model in this increment, call `model.predict(observation, action_masks=env.action_masks(), deterministic=...)`; document that omitting the mask is not a valid game-action protocol. Keep observation encoding, legal masks, and index-to-plan conversion in shared PPO adapters so later inference can reuse them.
- **REQ-005:** Provide a documented local training command with integer `--seed`, positive `--step-limit`, positive `--total-timesteps`, and valid PPO rollout/minibatch settings (`n_steps`, `batch_size`; `n_steps > 1`, `batch_size > 1`, `batch_size <= n_steps` for one environment). Defaults must allow a short bounded smoke run. Fix the opponent policy to the existing seeded random player. Report configuration and actual collected timesteps, episode counts and win/loss/draw/cutoff counts, episode length/return summaries, and SB3 update metrics (at least number of updates and policy/value/entropy losses). Do not present loss as evidence of skill.
- **REQ-006:** Define and document a reproducibility protocol: seed the model and NumPy/PyTorch through SB3's seed support, use one training environment, and derive a distinct deterministic environment seed for every episode (for example, `training_seed + episode_index`, with episode index reset when an explicit seed is passed to `reset`). When SB3 auto-resets with `seed=None`, continue that sequence rather than falling back to unseeded game randomness. Seed the Gym action space for standalone sampling. State the CPU/Python/dependency settings used for a reproducible short run; compare repeated short runs in the same configuration, without promising bitwise equivalence across platforms or hardware.
- **CON-001:** Keep core authoritative for game state, movement, combat, and victory; do not train through the API. Do not alter the fixed scenario, 01 reward, or the audited 02 observation/mask meaning to accommodate the trainer. Keep the random baseline available.
- **CON-002:** Pin a mutually compatible training dependency set separately from unrelated server dependencies: `sb3-contrib==2.7.0`, `stable-baselines3==2.7.0`, `gymnasium>=0.29.1,<1.3`, `torch>=2.3,<3`, and `numpy>=1.20,<3` (or tighter compatible pins if verified in the supported environment). Document install and execution from the repository root. Do not require the heavyweight trainer packages simply to import or run the random environment/inspector unless the repository's chosen dependency layout explicitly documents that tradeoff.
- **CON-003:** Decompose the Gym adapter and training entry point by responsibility; avoid a single module owning game transitions, normalization, logging, and CLI parsing. Before implementing any deviation from this numbered specification, explain it and its reason to the user and request a decision. Writing this specification does not mark 03 complete in the schedule or PPO vision.

## 4. Interfaces & Data Contracts

| Field | Gymnasium space | Value at a decision |
| --- | --- | --- |
| `occupancy` | `Box(low=-1, high=1, shape=(25,), dtype=int8)` | Existing row-major `-1` opponent / `0` empty / `1` learner encoding. |
| `defensive_fire_ready` | `MultiBinary(25)` | Existing row-major 0/1 readiness. |
| `remaining_steps` | `Box(low=0, high=step_limit, shape=(1,), dtype=int32)` | Remaining learner decisions, including 0 on a limit cutoff. |
| action | `Discrete(25)` | Index `row * 5 + column`; current learner cell is hold. |
| `action_masks()` | NumPy boolean array, shape `(25,)` | Current underlying `legal_action_mask`; all false after termination or truncation. |

`Dict` fields are passed to `MultiInputPolicy`; no core `GameStatus`, event log, RNG state, or future opponent choice enters the observation. Convert Gym-compatible NumPy integer actions to the underlying Python index after confirming they are scalar integers; illegal and out-of-range actions must still fail before game mutation. The underlying integer reward becomes a Gym-compatible numeric reward. The Gym adapter must satisfy `observation_space.contains(observation)` at reset, at each decision, and on endings. `info` retains the underlying transition diagnostics; episode summary fields use a documented namespace to avoid colliding with those diagnostics or SB3's conventional `info["episode"]` monitor field.

Proposed entry point (exact module name may differ if documentation and tests agree):

```sh
PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src python -m battle_agent_rl.ppo.train --seed 0 --step-limit 50 --total-timesteps 256 --n-steps 64 --batch-size 32
```

The trainer must use the adapter's native `action_masks()` recognized by SB3-Contrib. If wrapped or vectorized, preserve the mask method and episode-end information across wrappers; ordinary unmasked SB3 `PPO`, ordinary unmasked evaluation, and `predict` without `action_masks` do not meet this contract. Training may overshoot requested timesteps to finish an SB3 rollout; print the actual count.

## 5. Acceptance Criteria

- **AC-001:** Given a reset or active step, when sampling repeatedly through MaskablePPO with the adapter's mask, then every selected index is marked `True` and is accepted by the original environment; an invalid index fails without changing game state.
- **AC-002:** Given a core completion or a step-limit cutoff, when the adapter returns its last step, then termination/truncation, reward, last observation, all-false mask, and outcome summary agree with the 01 transition; the next seeded reset has a valid decision mask.
- **AC-003:** Given a short masked training run, when at least one PPO rollout and update finish, then update metrics and episode outcomes are visible, model parameters change from their initialized values, and masked predictions on multiple reachable decision states remain legal.
- **AC-004:** Given two runs with the same seed, config, software, and CPU execution settings, when training is repeated, then their episode seed sequence, short-run outcome/action trace and collected timestep count agree, and their resulting parameters/metrics agree within a stated numerical tolerance. Distinct episode resets within one run must not replay the same seed by accident.
- **AC-005:** Given the documented install and command, when run from the repository root, then the trainer completes without modifying the fixed scenario or blocking the random-policy inspector; full server-side checks pass.

## 6. Test Automation Strategy

Use `pytest` under `battle_agent_rl/tests/ppo`. Check the Gymnasium reset/step return contract, declared spaces and `observation_space.contains` at reset, active decisions and endings; choose step actions from the current mask and separately assert that an illegal `Discrete(25)` index is rejected without mutation. Do not run Gymnasium's generic `check_env` directly on this strict adapter: it samples from the unmasked action space and may select an illegal destination. Test masks against the existing environment on reset, an ordinary step, completion, cutoff, and reset after ending. Use a deliberately restricted mask or controlled decision to prove both rollout sampling and `predict(..., action_masks=...)` actually apply the mask rather than merely succeeding when most actions happen to be legal. Compare pre/post model parameters over a small real training update and inspect structured episode summaries instead of asserting particular losses or learned skill. Run two short CPU runs with the same seed and settings and compare recorded actions/outcomes and parameters with a documented floating-point tolerance. Keep training smoke work bounded (small network and rollout), avoiding lengthy convergence tests. Run `./server-side-checks.sh`; no win-rate threshold or GPU benchmark is required here.

## 7. Rationale & Context

The 02 audit found no remaining mutable decision signal missing for this fixed task and added `remaining_steps`, making finite-horizon cutoffs visible to the policy. A Gymnasium adapter isolates third-party framework interfaces from core-owned game logic. A boolean native mask is necessary both during MaskablePPO rollout collection and at prediction time; a legal action space declaration by itself does not mask logits. Episode summaries and optimizer metrics demonstrate that training occurs, while comparative skill measurement is deliberately deferred to 04.

## 8. Dependencies & External Integrations

- **DAT-001:** 01's `PPOTrainingEnvironment` and 02's audited observation/mask are the sole game transition and policy-input sources.
- **EXT-001:** `battle_hexes_core` supplies authoritative movement, combat, and outcome.
- **PLT-001:** Python 3.9+ with Gymnasium, NumPy, PyTorch, Stable-Baselines3, and matching SB3-Contrib versions as in CON-002. The version compatibility ranges are those declared by the 2.7.0 packages; verify the selected installation locally.
- No network service, API integration, deployment infrastructure, or compliance dependency is required at training time.

## 9. Examples & Edge Cases

- At reset with `step_limit=50`, the observation's `remaining_steps` is `np.array([50], dtype=np.int32)`; if the learner starts at `(2, 0)`, mask index 10 is hold. The mask is recalculated after the opponent turn, not copied from before combat.
- A one-step hold that leaves core status in progress returns `truncated=True`, `terminated=False`, reward `0`, `remaining_steps=[0]`, and summary outcome `cutoff`. A win on that same last step instead returns `terminated=True`, `truncated=False`, outcome `win`, and reward `+1`.
- `reset(seed=7)`, then an automatic `reset()` after an ending, starts episodes with game seeds 7 and 8 respectively under the example seed protocol. Explicit `reset(seed=7)` restarts the sequence. This makes vectorized auto-resets reproducible without repeating a single game forever.
- `model.predict(obs, action_masks=env.action_masks(), deterministic=True)` must be used for a standalone prediction. Predicting from an ending's all-false mask is invalid; reset first.

## 10. Validation Criteria

The adapter satisfies the targeted Gymnasium API/space checks and SB3-Contrib masked-learning checks described above, plus AC-001 through AC-004 with real masked learning and prediction; the documented command prints its configuration, outcome summaries, and update metrics. Dependency installation and `./server-side-checks.sh` pass. Record the short-run seed, CPU settings, library versions, and numerical tolerance alongside reproducibility evidence. After implementation and verified evidence, update the schedule and PPO vision as directed there; specification authorship alone does not count as completion.

## 11. Related Specifications / Further Reading

- [01 — Minimal training environment](01-training-environment.md)
- [02 — Rollout inspection and observation audit](02-rollout-inspection.md)
- [PPO implementation schedule](implementation-schedule.md)
- [PPO agent vision](../../battle_agent_rl/PPO.md)
- [Environment contract and observation audit](../../battle_agent_rl/PPO.md#evidence-and-observation-audit)
- [SB3-Contrib MaskablePPO documentation](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html)

## Open Questions

No questions.
