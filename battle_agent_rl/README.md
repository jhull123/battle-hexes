# Battle Agent RL

This package will host reinforcement learning based agents. It currently
contains a simple Q-learning prototype that can battle against a random
opponent.

See the `RLPLAN.md` file for information on the plan to develop various
RL agents.

## Minimal PPO training environment

`battle_agent_rl.ppo.PPOTrainingEnvironment(step_limit=50)`
provides `reset(seed)` and `step(action)`. Both return a `Transition` with
`observation`, `legal_action_mask`, `reward`, `terminated`, `truncated`, and
`info`. Call `reset` after either ending. Each step includes the learner's
movement, defensive fire and combat, followed by the opponent's complete turn
if the game is still active. The board is 5 rows by 5 columns, with one unit
per side and no core turn limit. The opponent samples sorted legal destinations
using the episode's private seeded RNG; combat and defensive fire share it.

The observation contains two fixed-length, 25-element tuples in row-major
order (`row * 5 + column`) and an integer `remaining_steps` equal to the
step limit minus the number of completed environment steps. `occupancy` is `1`
for the learner, `-1` for the opponent, or `0` for empty.
`defensive_fire_ready` is `1` when that cell's unit
is currently eligible for defensive fire, otherwise `0` (including empty
cells). For the active learner it describes readiness if its turn ended now;
for the off-turn opponent it describes whether it can fire on the learner's
move. This distinguishes board positions with different defensive-fire risk.
The mask has 25 booleans in the same order; the current cell is the hold
action. On an ending, the mask is all false. `info` contains the core `outcome`
(`GameStatus`), `turn_number`, `step_count`, the selected `(row, column)`
`destination` (or `None` on reset), and the current step's `defensive_fire`
and `combats` events.
These diagnostics are not policy inputs. Reward is +1 for a win, -1 for a loss,
and 0 for a draw or unfinished game. An environment step-limit cutoff is
`truncated`, with the core outcome still `in_progress`.

Baseline: across seeds 0–99, sampling uniformly from each mask using a
separate `random.Random(seed)` for the learning policy produced **36 wins / 100
episodes (36% win rate)**, **4.92 steps per episode** on average (44 losses,
20 draws; no cutoffs at the default 50-step limit). Reproduce with:

```python
import random
from battle_agent_rl.ppo import PPOTrainingEnvironment

for seed in range(100):
    env = PPOTrainingEnvironment()
    result = env.reset(seed)
    policy = random.Random(seed)
    while not (result.terminated or result.truncated):
        legal = [i for i, allowed in enumerate(result.legal_action_mask)
                 if allowed]
        result = env.step(policy.choice(legal))
```

## Seeded rollout inspection

From the repository root, run a complete game with the default seed `0`,
50-step limit and random policy:

```sh
./inspect-ppo-rollout.sh
```

For a deliberate one-step cutoff, or a different seed:

```sh
./inspect-ppo-rollout.sh --seed 42 --step-limit 1 --policy hold --expect-ending cutoff
./inspect-ppo-rollout.sh --seed 5
```

The script sets `PYTHONPATH` for you and forwards options to the inspector;
`./inspect-ppo-rollout.sh --help` lists them. `--seed` seeds the environment's
game and opponent RNG and a **separate** `random.Random(seed)` for the policy.
`random` uniformly samples the sorted
legal indexes; `hold` chooses the learner's current hex. The step limit must
be positive. `--expect-ending` is optional; a mismatch, invalid transition,
or environment error exits nonzero with a step-numbered diagnostic on stderr.
The repository checks run both fixed fixtures without printing successful
traces. `NO_COLOR=1` disables styling, as does redirecting stdout.

Each decision prints the pre-action board and row-major observation and mask,
the intended action, the step's fire and combat event collections, reward and
status, then the returned next decision or final state. Board rows and columns
are zero-based; `L` is learner, `O` opponent, `.` empty and `*` marks the
selected destination on the **pre-action** board. A final `L` is the actual
post-resolution location, which can differ after a retreat. Legal indexes are
shown alongside `(row, column)`; an empty event collection reads `none`.
Event collections do not establish a shared chronological order. `cutoff`
means the environment stopped while core status is `in_progress`, not a draw.

### Observation and mask audit (increment 02)

The inspector checks both observation planes cell by cell against core units,
readiness against `public_defensive_fire_status(learner)`, all 25 mask entries
against `get_reachable_hexes`, a core path for every legal action including
hold, and an all-false ending mask. It also checks the returned status, reward,
step/turn counts, ending flags and remaining horizon at reset and every step.
The visual trace is diagnostic; core state and `info` are not policy inputs.

| Current-state factor | Policy access / finding |
| --- | --- |
| Positions and unit elimination | Encoded by occupancy, including empty cells after combat. |
| Defensive-fire eligibility for each side | Encoded by readiness for the learner's decision; opponent off-turn eligibility affects incoming fire. |
| Movement legality (enemy occupancy, adjacency stop, reachable paths) | Derived from the complete legal mask; core paths checked for each `True` entry. Terrain/movement costs and fixed movement allowance are fixed in this scenario. |
| Unit attack, defense, movement allowance, faction, terrain, fire settings | Fixed by this scenario; not changing between decisions. |
| Movement points remaining and retreat/spent-fire flags | Their effects on current readiness are encoded in readiness; a new learner decision starts a fresh turn, and the opponent has finished its turn. Same visible positions/readiness/mask with different historical flags has no different next-action consequence in this fixed task. |
| Remaining steps before environment cutoff | **Now encoded** as `remaining_steps`. Before this correction, reset and a later return to the same positions/readiness could have identical policy inputs but different cutoff timing and terminal reward opportunities. For example, with a one-step limit, seed 42 holding at reset immediately cuts off; with a longer limit the same initial decision has additional turns available. |
| Core step/turn number, ending state, winner/reason, event records | Diagnostic-only `info`; terminal rewards and masks report endings, not future decision inputs. |
| Future opponent choices and combat/fire rolls | Private seeded randomness, not current-state observation features. |

**Contract change:** Added integer `remaining_steps` to the observation;
occupancy, readiness and mask retain their original meaning and shape. No mask
corrections were necessary. For the fixed 1v1 task, the audit found no further
missing mutable decision signal blocking increment 03.

## Training scripts

Two helper scripts start training sessions with the required `PYTHONPATH`:

```bash
./train_qlearning.sh
./train_multiunit_qlearning.sh
```

Each accepts the number of training episodes as an optional argument:

```bash
./train_qlearning.sh 10
./train_multiunit_qlearning.sh 10
```

You can also invoke the trainer modules directly:

```bash
python -m battle_agent_rl.qlearningplayer.qlearningtrainer 10
python -m battle_agent_rl.qmultiunittrainer 10
```
