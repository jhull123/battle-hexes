# Battle Hexes PPO Agent

## Status

The fixed 5×5, one-unit-per-side environment, seeded rollout inspector and
masked PPO training loop are implemented (see the
[schedule](../specs/ppo-agent/implementation-schedule.md)).
Core owns game rules; PPO uses SB3-Contrib `MaskablePPO` to learn legal
destinations. Training updates are verified, but improvement over a baseline
has not been established. Checkpoint evaluation and a core-compatible inference
player are later increments.

## Run locally

Use Python 3.12. From the repository root, after setting up `.venv312` as in
the [root README](../README.md#setting-up-the-api):

```sh
source .venv312/bin/activate
./inspect-ppo-rollout.sh --seed 0 --policy random --expect-ending completed
./inspect-ppo-rollout.sh --seed 42 --step-limit 1 --policy hold --expect-ending cutoff
python -m pip install -r requirements-ppo.txt
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src \
  python -m battle_agent_rl.ppo.train --seed 0 --step-limit 50 \
  --total-timesteps 256 --n-steps 64 --batch-size 32 \
  --inspect-episode 42
```

The inspector does not need trainer dependencies; run
`./inspect-ppo-rollout.sh --help` for options. `random` samples sorted legal
indexes with a policy-local `random.Random(seed)` separate from the game RNG;
`hold` keeps the learner in place. The trace shows the pre-action board,
observation, legal indexes/coordinates, action, defensive fire, combat, reward
and final state. `L` is learner, `O` opponent, `.` empty and `*` the chosen
destination, which can differ from the post-combat unit position. A cutoff
leaves core status in progress. `NO_COLOR=1` disables styling.

The environment's row-major 25-cell observation has `occupancy` (learner 1,
opponent -1, empty 0), `defensive_fire_ready` (0/1) and `remaining_steps`.
The boolean action mask marks legal destinations; the current cell is hold.
Rewards are +1 for a win, -1 for a loss and 0 otherwise. At an ending the mask
is all false; a step-limit cutoff is `truncated`, not a core draw. The Gym
adapter (`ppo.gym_env.MaskedBattleHexesEnv`) exposes the same inputs to
`MultiInputPolicy`. Always pass the current mask for prediction:
`model.predict(obs, action_masks=env.action_masks(), deterministic=True)`.

The trainer uses one CPU environment and a seeded random opponent. Explicit
`reset(seed=s)` starts game seed `s`; automatic resets advance to `s+1`,
`s+2`, etc. The Gym action space is seeded too. The CLI requires positive
`--step-limit` and `--total-timesteps`, `--n-steps > 1`, and
`1 < --batch-size <= --n-steps`; the values above are its defaults. It reports
actual collected steps (which may exceed the request), completed episode
outcomes/length/return and PPO update losses. Losses do not measure playing
skill. Optional `--inspect-episode SEED` uses the just-trained in-memory model
for one deterministic, mask-aware episode, bounded by `--step-limit`. It prints
each board, legal index and coordinate, selected action, reward and ending
through the same audited inspector as the random/hold baseline. The supplied
seed makes this spot check repeatable; the model is not saved here (checkpoints
belong to increment 04). Compare two identical training commands' summaries
and inspection traces, and inspect decisions where most destinations are
illegal: every printed PPO action must appear in that decision's legal list.

## Evidence and observation audit

Uniform random play over seeds 0–99 won 36, lost 44 and drew 20 games (mean
4.92 steps). The inspector verifies each observation and legal mask against
core, including after combat and at endings. For this fixed task:

| Decision factor | Policy access |
| --- | --- |
| Positions and eliminated units | Occupancy. |
| Defensive-fire eligibility | Readiness plane; includes opponent off-turn fire risk. |
| Legal movement and hold | Core-derived mask; every legal destination has a path. |
| Remaining time to cutoff | `remaining_steps`, added by the 02 audit. |
| Unit attributes, terrain and fire settings | Fixed by the scenario. |
| Movement/retreat history | Current readiness and positions capture its next-decision effects; new turns refresh movement. |
| Turn/status/event history | Diagnostic `info`, not policy input. |
| Future opponent choices and rolls | Private seeded randomness. |

No mask change was needed. A cutoff remains distinguishable from a completed
game even when its core status is `in_progress`. For reproducibility, two
seed-12 CPU runs (Python 3.12.3, Torch 2.5.1+cpu, NumPy 2.5.4, Gymnasium
1.2.3, SB3/SB3-Contrib 2.7.0, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`, limit 2,
32 timesteps, n_steps 16, batch size 8, [16, 16] network) matched action and
outcome traces and timesteps; parameters and update metrics agreed within
`rtol=1e-6, atol=1e-7`. Results need not match across hardware or versions.

## Direction

Keep training and inference on the same observation, mask and action-to-plan
mapping, with core authoritative for movement, combat and victory. Next select
checkpoints on validation seeds and measure win/loss/draw rates against random
and hold baselines on held-out games, then connect a frozen policy to the core
`Player` interface. Design multi-unit decisions and variable-sized inputs
before expanding the scenario; see the numbered specifications in the
[schedule](../specs/ppo-agent/implementation-schedule.md).
