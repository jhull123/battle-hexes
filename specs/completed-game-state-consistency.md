# Completed-Game State Consistency — Implementation Specification

## Overview

Fix the lifecycle transition at the end of a scenario's final turn so completed
games do not advance into a nonexistent next turn. For an eight-turn
**Crossroads on D-Day** game, the final response must remain on turn 8, expose
no active player or phase, preserve the completed result and scores, and reject
further gameplay mutations.

This specification covers the coordinated core, API, and frontend change. It
does not include implementation code or migration of existing completed games.

## Root cause

The current ordering in `battle_hexes_core/game/game.py` causes the inconsistent
state:

1. `Game.end_turn()` calls `next_player()` unconditionally.
2. When the last player ends a turn, `next_player()` wraps to Player 1,
   increments `turn_number`, resets the new player's movement and defensive-fire
   state, and evaluates game status.
3. `GameStatusEvaluator` recognizes the turn limit only when
   `turn_number > turn_limit`.
4. `end_turn()` then sets `current_phase` to `"movement"`.

An eight-turn game therefore becomes turn 9 with Player 1 in movement before it
is marked completed. API schemas and the frontend then expose those contradictory
fields alongside `gameStatus.state: "completed"`.

## Required behavior

### Final-turn boundary and scoring order

A turn-limit game completes when the last player in player order ends their turn
on the scenario's final numbered turn. Reaching turn 8 during movement or combat
must not end the game early; the final player must finish the turn.

Preserve the existing final scoring sequence:

1. Apply the submitted final board state.
2. Finish movement/combat scoring at its existing rule-defined point.
3. Recalculate scenario victory and final scores before evaluating the
   turn-ending result.
4. Evaluate completion while the game is still on the final player and turn.
5. If completed, do not call `next_player()`, increment the turn, reset another
   player's units, or initialize another movement phase.
6. Store and return the completed status using the finalized scores.

Earlier players ending their turns during turn 8 must still advance normally.
Immediate victory conditions continue to be evaluated at their existing points.

### Canonical completed state

All core and API projections must represent a completed game as:

| Field | Value |
| --- | --- |
| `gameStatus.state` | `"completed"` |
| `turnNumber` | Scenario turn limit (`8` for Crossroads on D-Day) |
| `activePlayer` | `null` |
| `currentPhase` | `null` |
| `pendingCombats` | `[]` |

The completed status must retain the final `winnerPlayerName`,
`winnerFactionId`, `reason`, and `message`. Scores and board state must remain as
they were when completion was evaluated.

Use nullable `activePlayer` and `currentPhase` because a completed game has no
player who may act and no actionable phase. Update all applicable API schemas
and serializers accordingly. This is a coordinated API and client change, with
no compatibility rollout required.

### Post-completion mutation rejection

The following endpoints must reject an already-completed game with HTTP
`409 Conflict` before applying request data or changing game state:

- `POST /games/{game_id}/movement`
- `POST /games/{game_id}/move`
- `POST /games/{game_id}/end-movement`
- `POST /games/{game_id}/combat`
- `POST /games/{game_id}/end-turn`

A rejected request must leave the board, scores, turn, player, phase, combats,
and game status unchanged. Core gameplay mutators should enforce the same
terminal-state invariant so API orchestration cannot bypass it.

## Implementation outline

### Core

Update `Game.end_turn()` and `GameStatusEvaluator` so turn-limit evaluation has
explicit turn-end context. Evaluation during movement and combat must not treat
`turn_number == turn_limit` alone as completion.

At the final player's final turn end, evaluate completion before rotation, keep
the turn at the limit, set the current player and phase to `None`, clear pending
combats, and return without next-turn resets. Preserve existing rotation, turn
increments, phase initialization, scoring, and defensive-fire behavior for
in-progress games.

### API

Guard every gameplay mutation endpoint immediately after loading the game. Keep
game-rule evaluation in core, not routes or schema modules.

Update `GameModel`, `MovementResponseModel`, and `SparseBoard` projections to
serialize completed `activePlayer` and `currentPhase` as JSON `null`. Ensure the
end-turn route and logging handle the absence of a next player. Successful
completion responses must include final scores and the full game status.

### Frontend

Treat `gameStatus.state === "completed"` as authoritative in the game model,
menu, and CPU-player flow. Applying a completed response must not locally
advance a phase, rotate a player, increment the turn, or start another action.

The UI must display `Turn 8 / 8` and a completed, non-actionable state; show no
active-player highlight or current phase; disable phase-ending actions; issue no
further gameplay requests; and retain the backend-provided winner, faction,
reason, and scores in the game-over presentation.

## Focused regression tests

### Core

- Ending the last player's turn at the limit completes without advancing the
  player or turn; ending an earlier player's turn still advances normally.
- Completed state has the final turn, null player/phase, and no pending combats.
- Winner, faction, reason, message, and final scores are preserved.
- Existing non-final turn behavior remains unchanged.

### API

- Final `end-turn` and subsequent GET return turn 8, null player/phase, empty
  combats, final scores, and the complete winner result.
- Each gameplay mutation endpoint returns 409 for a completed game, and a state
  snapshot before and after each rejected request is unchanged.

### Frontend

- Applying the completed response does not increment the turn or expose an
  active player or phase.
- The menu displays Turn 8 / 8, with no active movement phase or player badge.
- Human and CPU flows make no gameplay calls after completion.
- The game-over presentation retains winner, faction, reason, and score data.

Run:

```bash
./server-side-checks.sh
cd battle-hexes-web && npm run test-and-build
```

## Acceptance criteria

- The final player ending turn 8 completes Crossroads on D-Day without creating
  turn 9 or initializing Player 1's movement.
- Core and every API response report turn 8, null active player, null phase, and
  no pending combats while retaining final scores and completion details.
- All listed mutation endpoints reject completed games with 409 without changing
  state.
- The frontend displays no active movement state or Turn 9 and sends no further
  gameplay mutations after authoritative completed status is received.
- Relevant backend and frontend suites pass without changing in-progress
  gameplay behavior.

## Open Questions

No questions.
