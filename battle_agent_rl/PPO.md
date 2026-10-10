# Battle Hexes PPO Agent: Vision

## Purpose

Build a Battle Hexes player that learns from games through Proximal Policy
Optimization (PPO), then can make legal moves through the same core `Player`
interface as other computer players. This is an applied RL project as well as
an agent-development project: each increment should make the agent's decisions,
training behavior, and limitations understandable.

The [implementation schedule](../specs/ppo-agent/implementation-schedule.md)
orders the work. Individual numbered specifications define the contracts for
each increment. This vision describes the destination, not a fixed algorithm
or delivery date.

## Current state

The completed [01 training environment](../specs/ppo-agent/01-training-environment.md)
provides a seeded 5×5, one-unit-per-side game with legal destination masks,
observations, rewards, and clear terminal versus cutoff outcomes. A random
policy supplies a reproducible baseline. The completed
[02 rollout inspector](../specs/ppo-agent/02-rollout-inspection.md) provides
seeded, checked turn-by-turn traces, including combat, defensive fire and
cutoff outcomes. The observation audit added `remaining_steps` to the policy
input and found no mask correction necessary for this fixed task; see the
[usage and audit record](README.md#seeded-rollout-inspection). No PPO policy or
training update exists yet; the current `LearningPlayer` only passes a
selected movement plan to core.

## Desired experience

- Inspect a seeded game turn by turn: board, observation, legal actions, chosen
  move, combat and defensive fire, reward, and episode outcome.
- Train a masked PPO policy on the small scenario and see whether its behavior
  changes, not just whether an optimization loop runs.
- Select frozen checkpoints using validation seeds, then compare the selected
  policy with declared baselines on separate, held-out seeds. Report
  win/loss/draw rates, episode length, and uncertainty rather than a favorable
  training run alone.
- Load a trained policy into a core-compatible `PPOPlayer` for local games. The
  game engine remains authoritative for legal movement and combat.
- Expand to richer scenarios only after the action and observation contracts
  for multiple units are deliberately designed and tested.

## Architectural boundaries

- `battle_hexes_core` owns game rules, transitions, legal paths, and victory.
  PPO code must not reproduce these rules or train through the HTTP API.
- `battle_agent_rl.ppo` owns the environment, observation/action adapters,
  training and evaluation entry points, checkpoint handling, and inference
  player. Keep these responsibilities in cohesive modules as they appear.
- Training and inference must use the same observation encoding, legal-action
  masking, and action-to-plan mapping. A policy should never be asked to learn
  from an action that the game will reject.
- Keep randomness seedable: a fixed game seed and fixed policy/action sequence
  should reproduce an environment trajectory. Across different evaluation
  seed sets, expect statistically consistent estimates rather than identical
  outcomes. Keep the random policy as a baseline, not a learning agent.
- Keep rewards and episode endings tied to authoritative game status. Begin
  with the existing terminal reward; add shaping only to address an observed
  learning problem and evaluate for unintended incentives.
- Use [SB3-Contrib's `MaskablePPO`](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html)
  for the policy, masked action sampling, and PPO updates. Do not reimplement
  the PPO optimizer in this project. Battle Hexes owns the game adapter,
  observation/action mapping, training entry point, and evaluation protocol.
  Choose compatible dependency versions and the exact adapter contract in 03.

## Evidence of progress

A working trainer is not yet a successful agent. First prove reproducible
policy updates that sample only legal actions; then show improvement over a
predeclared baseline across held-out games. Checkpoints, training curves,
and representative rollout traces should make regressions visible. Later
milestones must also prove that the frozen policy behaves the same way through
the core `Player` interface as it did in evaluation.

## Decisions intentionally deferred

- How one policy decision should order multiple units: one unit at a time,
  a complete turn, or another explicit scheme.
- How larger maps and varying unit counts fit a stable policy input/output
  contract, and when a trained player should be exposed through the API/UI.

These decisions belong in focused specifications after the small environment
has been observed and measured. The older `RLPLAN.md` surveys many RL methods;
it is not the implementation schedule for this PPO track.
