# PPO Agent 01: Minimal Training Environment

## Goal

Provide a small, testable turn-based environment that a PPO trainer can drive.
This first increment proves the game-to-learning boundary with a random policy;
it does **not** train a neural policy.

## Scope

- Use a fixed, small, one-unit-per-side elimination scenario. The learning side
  plays against a random legal-move opponent.
- Implement the environment in `battle_agent_rl`, using public
  `battle_hexes_core` game operations. Do not add RL methods to core `Player` or
  route training through the HTTP API.
- Retain `RandomPlayer` as a baseline and reuse its reachable-hex and path
  concepts. Do not copy its random choice into the learning policy.
- Exclude multi-unit orders, self-play, reward shaping, model training, and UI
  integration from this increment.

## Environment contract

Expose `reset(seed)` and `step(action)` with a stable, documented result:
observation, legal-action mask, reward, `terminated`, `truncated`, and
diagnostic information. A reset starts a fresh game with fresh mutable units,
players, and board; no state from the previous episode may leak into it. The
learning side is always the side to act when an observation is returned, unless
the episode has ended.

An action is one destination on the fixed board, indexed in row-major order.
The current hex represents **hold**. The mask marks exactly the current hex
and destinations legally reachable by the learning unit at that decision point;
all other indexes are invalid. Convert a selected destination to a
`UnitMovementPlan` using core pathfinding. Reject an invalid or out-of-range
action before mutating game state. Keep observation and mask shapes fixed for
the scenario; document each observation field and its normalization when the
environment is implemented. Observation data must come from game state, not
from callback timing or a cached previous turn.

One `step` executes the learning side's movement and all resulting combat, then
the random opponent's complete turn if the game remains active. Return the next
learning-side decision state, or the final state. Use core game-status and
winner information after combat and turn advancement; do not infer the outcome
from a hard-coded unit count. Refresh status after combat before reporting an
outcome. Resolve and surface defensive-fire effects as part of the same step.

Reward is `+1` for a learning-side win, `-1` for a loss, and `0` otherwise,
including a draw. No intermediate shaping. `terminated` means the game reached
an authoritative completed state; `truncated` means an explicit environment
step limit was reached while the game was still in progress. A limit cutoff
must never be reported as a game result. Calls to `step` after either ending
must fail clearly until `reset`.

The seed controls both the random opponent and any scenario/game randomness
that affects repeatability. Legal destinations must be ordered deterministically
before sampling; do not depend on set iteration order or process-global RNG
state. Current combat and defensive-fire rolls use module-level randomness;
introduce narrow RNG injection at those core seams as needed, without changing
their rules. The diagnostic result includes at least outcome, turn/step count,
and the chosen destination, without becoming part of the policy observation.

## Player boundary

The learning player's `movement()` remains a core-compatible adapter that
returns movement plans. The environment supplies its selected action before
calling it. `movement_cb()` fires before combat and therefore must not finalize
reward. `combat_results()` may collect diagnostics but must not independently
advance the episode. The environment owns transition assembly and terminal
classification; `end_game_cb()` is not a terminal signal because the existing
`GamePlayer` also calls it on a turn-limit cutoff. The environment should drive
turns explicitly rather than use `AgentTrainer` or `GamePlayer.play()` as its
step API.

## Acceptance checks

- Every action marked legal produces a valid movement plan; invalid actions
  leave the game unchanged. Hold is always available while the unit can act.
- A seeded random policy completes many episodes without illegal moves,
  exceptions, or unbounded episodes; repeated seeds reproduce trajectories.
- A test covers a win, a loss, and a limit cutoff, distinguishing `terminated`
  from `truncated` and checking rewards against core game status.
- A test covers combat or defensive fire changing the board during a step, so
  the returned observation and outcome reflect the post-resolution state.
- Existing core and RL checks still pass. Record random-policy win rate and
  episode length as the baseline for the later PPO increment.

## Open Questions

No questions.
