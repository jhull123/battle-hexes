---
title: "PPO Agent 02: Rollout Inspection and Observation Audit"
date_created: 2026-10-10
tags: [design, ppo, reinforcement-learning]
---

# Introduction

Make a complete seeded episode of the existing 5×5, one-unit-per-side environment readable one decision at a time, and check whether its observation and legal-action mask adequately describe the current decision. This increment supplies evidence for designing the first trainer; it does not train a policy.

## 1. Purpose & Scope

This specification applies to `battle_agent_rl.ppo` and its local documentation and tests. The intended readers are implementers of the rollout inspector and the subsequent masked PPO trainer. Use the environment delivered by [01](01-training-environment.md), with its existing rules, fixed board, seeded opponent, terminal rewards, and explicit step limit. The inspector is a local command-line tool (or an equivalently reproducible local view), not a new game UI or a game engine.

## 2. Definitions

- **Episode:** One `reset(seed)` followed by zero or more `step(action)` calls until `terminated` or `truncated`.
- **Decision state:** The observation and legal-action mask returned by reset or a non-ending step, before the next learner action.
- **Action:** A row-major destination index `row * 5 + column`; selecting the learner's current hex means hold.
- **Observation:** The policy-visible `occupancy` and `defensive_fire_ready` 25-element arrays returned by the environment. Occupancy is `1` for the learner, `-1` for the opponent, and `0` for empty; readiness is `1` for an eligible unit and `0` otherwise.
- **Mask:** The 25-element `legal_action_mask`; `True` means the destination is legal at this decision. An ending transition has an all-false mask.
- **Ending:** `terminated` denotes completed core game status; `truncated` denotes an environment step-limit cutoff while core status is still in progress.
- **Audit:** A comparison of policy-visible inputs against current authoritative game state and core-derived legal movement, with findings documented explicitly.

## 3. Requirements, Constraints & Guidelines

- **REQ-001:** Provide a documented local invocation accepting an episode seed and positive step limit. A built-in random policy must sample uniformly from the sorted legal action indexes using a policy-local `random.Random(seed)`, separate from the environment's seeded game/opponent RNG. A hold-only policy is recommended to make cutoff traces easy to reproduce. Any manual action option must reject illegal choices through the environment's normal validation.
- **REQ-002:** Print the seed, step limit, policy, and initial decision state; for each step print the *pre-action* board, policy-visible observation, legal destination indexes and `(row, column)` coordinates, selected index and destination, then the returned reward, events, and ending/status. Print the returned board/observation and mask as the next decision state, or as the final state if ended. Label pre-action and post-step values distinctly.
- **REQ-003:** Render the board with row/column labels and an explicit learner/opponent/empty legend. Render observation arrays and mask in row-major order or with unambiguous index-to-cell labels so a reader can cross-check every cell. Distinguish the chosen destination from the final learner location: defensive fire or combat may move or remove a unit.
- **REQ-004:** Display defensive-fire and combat events for the step using the environment's `info["defensive_fire"]` and `info["combats"]` and their core result fields. Show relevant participants, outcome, and locations where available; explicitly show `none` when empty. Do not claim an event belongs to a particular side or imply a cross-type chronological order unless that information is actually captured; if side attribution is added, obtain it at resolution time rather than inferring it from the final board.
- **REQ-005:** Display the returned reward, step and turn numbers, `terminated`, `truncated`, and core `outcome` state, winner and reason (if present). A cutoff must be labeled as a cutoff with core status `in_progress`, not as a draw. Stop after an ending; no extra `step` call.
- **REQ-006:** Audit both the observation and mask at reset, during nonterminal play, and on endings. Compare each occupancy and readiness cell with the current board and core unit readiness for the learner's decision; compare each `True` mask entry with core-reachable destinations and a valid core path, including hold. Verify terminal/cutoff masks are all false. Trace output must reflect post-resolution state, not a cached pre-combat position.
- **REQ-007:** Document an audit record alongside usage instructions. List each currently relevant game-state factor considered (at least positions, defensive-fire readiness, movement legality, any mutable unit state that can affect the next action or its consequences, and remaining steps to cutoff). For each, state whether it is encoded in the observation, derived from the mask, fixed by this scenario, diagnostic-only, or missing; explain any missing factor's effect with a concrete reachable example or why it has no effect. Record any observation/mask changes made, or explicitly record that none were needed. Do not silently add features to the policy input based only on the visual trace.
- **CON-001:** Core owns rules, legal movement, combat and victory. The inspector must use `PPOTrainingEnvironment.reset`/`step` and authoritative board/status and transition data; it must not implement a parallel transition or reward calculation. Keep inspection code separate from environment state transitions.
- **CON-002:** Keep this increment limited to inspection and the observation/mask corrections justified by the audit. Preserve the fixed one-unit-per-side task and the existing random baseline as a comparison point; if an observation correction changes the public contract, update its documentation and focused tests before 03. No PPO trainer, checkpoint evaluation, or API/UI integration belongs here.
- **CON-003:** Before implementing any deviation from this specification, describe the proposed change and reason to the user and request a decision. After the increment meets its completion criteria, mark 02 done in the implementation schedule with delivered work and evidence, and update `battle_agent_rl/PPO.md` to reflect the current state.
- **GUD-001:** Prefer a compact text trace with a stable field order. Rendering is diagnostic, not an additional policy input. Do not expose random rolls or future opponent choices as observation features.

## 4. Interfaces & Data Contracts

Suggested entry point from the repository root (the exact module path may differ if documented consistently):

```sh
PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src python -m battle_agent_rl.ppo.rollout_inspection --seed 0 --step-limit 50 --policy random
PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src python -m battle_agent_rl.ppo.rollout_inspection --seed 42 --step-limit 1 --policy hold
```

`--seed` is an integer; `--step-limit` is a positive integer; `--policy` selects `random` or `hold` if both are provided. Reject invalid arguments with a clear nonzero exit. The first command uses the same policy sampling protocol as the baseline in `battle_agent_rl/README.md`; the second provides a deliberate short horizon. These are proposed invocation contracts, not claims that the commands already exist.

Consume the existing `Transition` contract: `observation`, `legal_action_mask`, `reward`, `terminated`, `truncated`, and `info` (`outcome`, `turn_number`, `step_count`, `destination`, `defensive_fire`, `combats`). The chosen action index comes from the policy, whereas `info["destination"]` is its `(row, column)` destination on the returned step; reset has destination `None`. `info` and the core board may be rendered for inspection but are not policy inputs. When rendering combat and fire events, use the fields actually present on core events rather than serializing mutable unit objects as if they were historical snapshots.

Each printed step follows this logical layout (exact typography is not contractual):

```text
episode: seed=0 step_limit=50 policy=random
decision: step=0 turn=1
board: [5 labeled rows; L=learner, O=opponent, .=empty]
observation: occupancy=[25 row-major values] defensive_fire_ready=[25 values]
legal: [index -> (row,column), ...]     # includes hold at learner position
action: index -> (row,column)
result: defensive_fire=[...] combats=[...] reward=0
ending: terminated=False truncated=False outcome=in_progress winner=None reason=None
next decision / final state: board=... observation=... legal=...
```

On a cutoff the final line must still show the actual board/observation, an empty legal list, reward `0`, `truncated=True`, and `outcome=in_progress`. A completed game has `terminated=True`, `truncated=False`, an empty legal list, and reward consistent with the reported winner.

## 5. Acceptance Criteria

- **AC-001:** Given the same seed, policy, step limit, and environment version, when the command is run twice, then the sequence of selected actions, board states, events, rewards, and endings is identical; random selection uses only actions marked legal.
- **AC-002:** Given a seed that reaches a completed game, when its trace ends, then the final board/observation and event records agree with the returned transition and core game state; its winner and reward agree with core status.
- **AC-003:** Given `--step-limit 1` and a hold-only policy on a still-active game, when the one step completes, then the output reports a cutoff, `reward=0`, an all-false mask, and core `outcome=in_progress` without presenting a winner or draw.
- **AC-004:** Given a movement that triggers defensive fire or combat, when the result is printed, then the event is visible and the returned board/observation show post-resolution unit positions or removals; the intended destination is still identifiable.
- **AC-005:** Given an active decision, when each visible legal destination is checked, then its row-major index matches the displayed coordinate and a core path exists; invalid and occupied enemy destinations are not printed as legal. The audit record explicitly evaluates possible missing mutable inputs and reports findings, including whether changes are necessary before 03.

## 6. Test Automation Strategy

Use focused Python tests under `battle_agent_rl/tests/ppo` for formatting/selection through the public inspection entry point or equivalent view, with real seeded environment transitions. Check deterministic replay, legality of displayed actions, consistency of pre/post observations with the board, one completed episode, one cutoff, and an event-bearing transition. Avoid asserting an entire formatted transcript when checking structured values or selected lines is sufficient. Use a controlled game state or seed for event coverage; do not rely on an unbounded random search. Run `./server-side-checks.sh` for affected Python packages. No performance benchmark or minimum coverage percentage is required for this small local tool.

## 7. Rationale & Context

The environment already returns a masked row-major destination space, two observation planes, step diagnostics, and seeded outcomes. A readable trace makes it possible to distinguish a chosen destination from its eventual outcome and see defensive fire before treating training metrics as evidence of agent quality. The audit checks whether two decisions that look identical to the policy can differ in legal actions or consequences because of current state omitted from its inputs. It does not assume every core field must be exposed: fixed scenario constants and private future randomness are different from missing decision-relevant mutable state. Findings can motivate a small correction now or an explicit follow-up before training.

## 8. Dependencies & External Integrations

- **DAT-001:** The 01 environment and `Transition` from `battle_agent_rl.ppo` provide episodes, mask, observation and diagnostics.
- **PLT-001:** Python standard-library command-line parsing, formatting and local seeded random generation suffice; no training framework or network service is required.
- **EXT-001:** `battle_hexes_core` provides board, unit readiness, legal movement, combat/defensive-fire events and authoritative game status.
- No third-party services, infrastructure or compliance integrations are required.

## 9. Examples & Edge Cases

- Initial learner location `(2, 0)` corresponds to action index `10` on the 5×5 board; selecting `10` is hold, not an omitted move.
- A defensive-fire retreat can leave the selected destination empty. Print both the selected index/destination and the post-step board instead of reporting the destination as the final location.
- Events may be absent even on a completed step; show `none` rather than fabricating combat. Events from both turns may occur in a single environment step, and separate event collections do not by themselves establish a shared chronological ordering.
- If a core completion and the step limit coincide, `terminated` takes precedence over `truncated`; do not turn a real win/loss/draw into a cutoff.

## 10. Validation Criteria

The delivered documentation includes copyable commands for a seeded completed episode and a seeded cutoff, the policy and seed protocol, the trace legend, and the completed audit record. Focused tests demonstrate the acceptance criteria against authoritative transitions; Python checks pass. Any confirmed missing current-state signal or incorrect mask is fixed and documented here or recorded as a specific blocker for 03, with a reproducible example and expected contract change. Proposed deviations are resolved with the user before implementation. Once completion is verified, the schedule records 02 as done and the PPO vision describes the newly delivered capability.

## 11. Related Specifications / Further Reading

- [01 — Minimal training environment](01-training-environment.md)
- [PPO implementation schedule](implementation-schedule.md)
- [PPO agent vision](../../battle_agent_rl/PPO.md)
- [RL environment contract and baseline](../../battle_agent_rl/README.md#minimal-ppo-training-environment)

## Open Questions

No questions.
