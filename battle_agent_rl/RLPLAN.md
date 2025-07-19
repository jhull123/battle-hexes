# Reinforcement Learning Plan for Battle Hexes

This document outlines the incremental plan for implementing reinforcement
learning (RL) agents for Battle Hexes, progressing from simple to complex
techniques. The goal is to build agents that can reason strategically in a
turn-based fantasy or historical combat environment.

---

## 🔹 Level 1: Foundations & Baselines

### ✅ 1. Random Agent
- Selects actions randomly.
- Useful for sanity checking environment integration and action validity.

### ✅ 2. No-Op Agent
- Takes no action on its turn.
- Useful for validating turn transitions and testing game stability.

---

## 🔹 Level 2: Tabular Methods

### 🔜 3. Q-Learning (Tabular)
- Off-policy value-based learning.
- Updates:  
  `Q(s, a) ← Q(s, a) + α [r + γ max_a′ Q(s′, a′) − Q(s, a)]`
- Best for small, discretized environments (e.g. fixed-size boards with limited units).

### 4. SARSA (Tabular)
- On-policy alternative to Q-learning.
- May perform better in situations requiring conservative learning.

---

## 🔹 Level 3: Function Approximation

### 5. Deep Q-Networks (DQN)
- Uses neural network to approximate Q-values.
- Integrates experience replay and target networks for stability.

### 6. Double DQN / Dueling DQN
- Double DQN: Addresses Q-value overestimation.
- Dueling DQN: Separates state-value and advantage functions for better generalization.

---

## 🔹 Level 4: Policy Gradient Methods

### 7. REINFORCE (Vanilla Policy Gradient)
- Directly optimizes the policy via episode returns.
- High variance, but conceptually simple.

### 8. Actor-Critic
- Combines policy (actor) and value function (critic).
- Provides more stable learning than REINFORCE.

### 9. Advantage Actor-Critic (A2C)
- Improves Actor-Critic with advantage estimates:
  `A(s, a) = R − V(s)`
- Effective for moderate complexity environments.

---

## 🔹 Level 5: Advanced Techniques

### 10. Proximal Policy Optimization (PPO)
- A robust and stable policy-gradient method.
- Useful in complex and stochastic environments.

### 11. Monte Carlo Tree Search (MCTS) + RL
- Combine search-based planning with neural policy/value networks.
- Strategy used in AlphaZero-style agents.

### 12. Multi-Agent RL (MARL)
- Required when both sides use learning agents.
- Techniques: self-play, centralized critics, shared policies.

---

## 🔹 Cross-Cutting Techniques

- **Reward shaping**: Adjust reward signals to guide desired behaviors.
- **Exploration strategies**: ε-greedy, entropy bonuses, softmax.
- **Curriculum learning**: Gradually increase difficulty.
- **Imitation learning**: Pretrain from human or scripted agents.
- **Model-based RL**: Learn environment dynamics for planning.

---

## ✅ Suggested Development Path

1. ✔ Random and No-Op agents (already implemented).
2. 🔜 Implement tabular Q-learning agent on a simplified game board.
3. 🧱 Define an abstract `RLPlayer` interface with `act`, `observe`, `train_step`.
4. ⚙️ Scale up to DQN once state/action space becomes large.
5. 🎯 Experiment with policy-gradient methods (REINFORCE, A2C).
6. 🤖 Add self-play training with PPO.
7. 🧠 Explore MCTS or multi-agent learning for advanced strategic behaviors.

---

## Notes

- Focus initially on limited-scale versions of the game (e.g. 2 units, small map).
- Save gameplay data for future use in imitation learning or debugging.
- Integrate training loop into battle_hexes_api or a standalone training script.
