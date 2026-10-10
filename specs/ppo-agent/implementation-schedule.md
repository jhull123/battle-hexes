# PPO Agent Implementation Specification Schedule

## Purpose

Divide the [PPO vision](../../battle_agent_rl/PPO.md) into small increments
that can be understood, implemented, and verified independently. The numbers
also name the focused specifications (`01-`, `02-`, and so on). This is a
dependency order, not a calendar or a promise that later designs are settled.
Only write a numbered specification when its increment is ready to be designed.

When an increment is implemented and its completion evidence is verified, mark
it done here with a link to the specification, delivered work, and evidence;
update the [PPO vision](../../battle_agent_rl/PPO.md) to reflect the new current
state. Writing a specification does not complete the increment. Raise proposed
deviations from a numbered specification to the user for a decision before
implementing them.

## Principles

- Preserve a runnable random baseline. Distinguish replaying one trajectory
  under fixed seeds and actions from comparing estimates across seed sets.
- Show what the environment and policy do before increasing game complexity.
- Keep core rules authoritative and PPO-specific code under
  `battle_agent_rl.ppo`; share observation/action conversion between training
  and inference.
- Define a measurable completion gate for each increment. A passing test suite
  or decreasing training loss alone is not evidence of a better player.
- Revisit later increments when measured behavior challenges an assumption;
  do not grow the fixed 1v1 environment into a collection of scenario switches.

## Increments

### 01 — Minimal training environment (done)

**Specification:** [01-training-environment.md](01-training-environment.md).

**Delivered:** A 5×5 one-unit-per-side environment, legal destination mask,
observation with occupancy and defensive-fire readiness, seeded opponent and
game randomness, terminal rewards, cutoff handling, and a random-policy
baseline. PPO source and tests live in dedicated `ppo` directories. Merged into
`feat/371-ppo-agent` through PR #373.

**Evidence:** Core/RL/API checks pass; seeded random rollouts reproduce the
documented baseline of 36 wins, 44 losses, and 20 draws in 100 games. No
learning takes place in this increment.

### 02 — Rollout inspection and observation audit

**Specification:** [02-rollout-inspection.md](02-rollout-inspection.md).

**Objective:** Make one seeded environment episode legible before training.

**Scope:** A small CLI or equivalent local view shows the board, policy-visible
observation, legal destinations, selected action, combat/defensive-fire events,
reward, and ending at each step. It uses a random or manually selected policy;
it is not a PPO trainer or a new game UI. Audit whether relevant current game
state is missing from the observation or action mask.

**Completion evidence:** A documented command reproduces a trace for a seed;
the displayed values match the environment transition and authoritative game
state, including a terminal game and a cutoff.

**Dependencies:** 01.

### 03 — First masked PPO training loop

**Planned specification:** `03-masked-ppo-training.md`.

**Objective:** Train a policy on the fixed 1v1 environment without changing
game rules or broadening the scenario.

**Scope:** Adapt the fixed environment to the Gymnasium contract required by
SB3-Contrib's `MaskablePPO`, including fixed observation/action spaces and an
action mask where `True` means legal. Use its masked policy, rollout collection,
and PPO updates rather than implementing those algorithms here. Define
compatible dependency versions, seeding, a repeatable training command, and
the boundary between the trainer and game-compatible player.

**Completion evidence:** Focused checks establish valid sampled actions,
masking during learning and prediction, parameter updates, and reproducible
short runs. Training output exposes episode outcomes and update metrics, but
does not claim skill from training loss alone.

**Dependencies:** 01 and 02; incorporate any observation fixes found in 02.

### 04 — Evaluation, visualization, and checkpoints

**Planned specification:** `04-evaluation-and-checkpoints.md`.

**Objective:** Determine whether training produces a better policy and make
progress and regressions visible.

**Scope:** Freeze and reload checkpoints; use SB3-Contrib's mask-aware
evaluation utilities to compare against random and no-op baselines. Chart or
tabulate win/loss/draw rates and episode lengths over training. Define no-op
as choosing hold on every learner turn; it does not
disable opponent actions, combat, or defensive fire. Fix the opponent policy,
opponent/environment randomness protocol, seed sets, and success criterion
before comparison. Select checkpoints on validation seeds; reserve a separate
held-out seed set for final reporting, not checkpoint selection.

**Completion evidence:** A saved policy reloads with the same legal-action
behavior. A fixed checkpoint and evaluation seed/RNG configuration reproduces
its reported metrics; independent seed sets yield statistically consistent
estimates. The final held-out report distinguishes improvement from noise or
overfitting without reusing its games to choose the checkpoint.

**Dependencies:** 03. Basic update metrics belong in 03; this increment adds
reliable evaluation and durable artifacts.

### 05 — Inference player in core games

**Planned specification:** `05-inference-player.md`.

**Objective:** Use a frozen policy through the ordinary core `Player` contract.

**Scope:** A `PPOPlayer` loads a compatible checkpoint, constructs the same
observation and mask used in training, selects a legal action, and returns a
`UnitMovementPlan` from `movement()`. Keep learning and reward bookkeeping in
training code, not player callbacks. Start with local 1v1 games; API/UI
exposure is separate.

**Completion evidence:** Seeded local games show the same frozen-policy choices
through evaluation and `PPOPlayer`, with legal plans, combat, and turn handoff
working through core.

**Dependencies:** 03 and 04.

### 06 — Multi-unit decision design and scenario growth

**Planned specification:** `06-multi-unit-design.md`.

**Objective:** Choose and prove an action/observation contract for more than
one unit before widening the training task.

**Scope:** Compare per-unit decisions, whole-turn orders, and other viable
schemes against legal movement, turn timing, variable unit counts, masking,
credit assignment, and policy input size. Prototype the selected contract on a
small multi-unit scenario; then plan broader scenarios or self-play separately.

**Completion evidence:** A reviewed contract and focused prototype demonstrate
legal complete turns and stable observations across the supported cases.
Training performance is a later gate, not proof of this design alone.

**Dependencies:** Learnings from 02–05. Do not assume the 1v1 action index
extends unchanged.

## Later activation

Connecting a trained player to the API/UI, broader scenarios, self-play, or
reward shaping requires separate specifications when their prerequisites and
success criteria are clear. None is silently included in the first trainer.

## Open Questions

No questions.
