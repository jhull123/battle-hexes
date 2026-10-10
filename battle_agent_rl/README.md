# Battle Agent RL

Reinforcement-learning agents for Battle Hexes. The Q-learning prototype plays
against a random opponent; see [RLPLAN.md](RLPLAN.md) for its broader plan.

For the seeded environment, rollout inspector, masked PPO trainer and current
limitations, see [PPO.md](PPO.md).

## Q-learning scripts

From the repository root, start a training session with
`./battle_agent_rl/train_qlearning.sh` (or pass an episode count, e.g.
`./battle_agent_rl/train_qlearning.sh 10`). The script sets `PYTHONPATH` for
the sibling packages.
