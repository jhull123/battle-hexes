# Battle Agent RL

This package will host reinforcement learning based agents. It currently
contains a simple Q-learning prototype that can battle against a random
opponent.

See the `RLPLAN.md` file for information on the plan to develop various
RL agents.

## Running the training demo

The script `train_qlearning.sh` starts a small training session using the
`QLearningPlayer` against a `RandomPlayer`.  It sets up `PYTHONPATH` so the
uninstalled packages can be imported correctly.

```bash
./train_qlearning.sh
```

The number of training episodes can be passed as an argument:

```bash
./train_qlearning.sh 10
```

