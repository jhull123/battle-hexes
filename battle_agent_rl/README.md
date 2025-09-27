# Battle Agent RL

This package will host reinforcement learning based agents. It currently
contains a simple Q-learning prototype that can battle against a random
opponent.

See the `RLPLAN.md` file for information on the plan to develop various
RL agents.

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
