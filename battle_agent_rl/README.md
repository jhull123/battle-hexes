# Battle Agent RL

This package will host reinforcement learning based agents. It currently
contains a simple Q-learning prototype that can battle against a random
opponent.

See the `RLPLAN.md` file for information on the plan to develop various
RL agents.

## Minimal PPO training environment

`battle_agent_rl.ppo_environment.PPOTrainingEnvironment(step_limit=50)`
provides `reset(seed)` and `step(action)`. Both return a `Transition` with
`observation`, `legal_action_mask`, `reward`, `terminated`, `truncated`, and
`info`. Call `reset` after either ending. Each step includes the learner's
movement, defensive fire and combat, followed by the opponent's complete turn
if the game is still active. The board is 5 rows by 5 columns, with one unit
per side and no core turn limit. The opponent samples sorted legal destinations
using the episode's private seeded RNG; combat and defensive fire share it.

The observation contains one fixed-length field: `occupancy`, a 25-element
tuple in row-major order (`row * 5 + column`). Each cell is normalized to
`1` for the learner, `-1` for the opponent, or `0` for empty. The mask has
25 booleans in the same order; the current cell is the hold action. On an
ending, the mask is all false. `info` contains the core `outcome` (`GameStatus`),
`turn_number`, `step_count`, the selected `(row, column)` `destination` (or
`None` on reset), and the current step's `defensive_fire` and `combats` events.
These diagnostics are not policy inputs. Reward is +1 for a win, -1 for a loss,
and 0 for a draw or unfinished game. An environment step-limit cutoff is
`truncated`, with the core outcome still `in_progress`.

Baseline: across seeds 0–99, sampling uniformly from each mask using a
separate `random.Random(seed)` for the learning policy produced **36 wins / 100
episodes (36% win rate)**, **4.92 steps per episode** on average (44 losses,
20 draws; no cutoffs at the default 50-step limit). Reproduce with:

```python
import random
from battle_agent_rl.ppo_environment import PPOTrainingEnvironment

for seed in range(100):
    env = PPOTrainingEnvironment()
    result = env.reset(seed)
    policy = random.Random(seed)
    while not (result.terminated or result.truncated):
        legal = [i for i, allowed in enumerate(result.legal_action_mask)
                 if allowed]
        result = env.step(policy.choice(legal))
```

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
