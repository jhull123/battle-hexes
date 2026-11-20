# 01 - No-op scripted player

## Goal

Deliver the first playable slice of the [scripted objective-seeking player (#407)](https://github.com/jhull123/battle-hexes/issues/407).
A user can select a **Scripted Player**, start or reload a game, and see it
automatically finish its turn without issuing any unit movement orders. Later
increments will replace the empty movement policy without changing how users
select or play against it.

## Player contract

- Add the player type ID `scripted` and label **Scripted Player** to
  `GET /player-types`. Use that stable ID for game creation, saved player
  configuration, and the API's `playerTypeIds`. Keep the core player category
  `PlayerType.CPU` (wire value `Computer`), not a new control category.
- Add a concrete core `Player` implementation in `battle_agent_rl.scripted`.
  Its `movement()` returns an empty list of `UnitMovementPlan`s for any board
  state. Its `combat_results()` callback does nothing; use the inherited no-op
  callbacks for movement and game completion. The policy does not mutate game
  state, consume randomness, or require objectives, a particular faction,
  board, or seat. Importing and running it requires only ordinary Python and
  the core game interfaces, not ML libraries.
- Reuse the existing CPU player factory and game-state hydration paths: the
  factory must reconstruct the scripted implementation from the saved type ID,
  not from the generic `Computer` category. Extend saved-player type validation;
  no new policy state, document version, or migration is needed. Existing
  saved games and player type IDs keep their current behavior.

## Scenario availability

- Offer **Scripted Player** on every scenario wherever a regular CPU player
  is allowed, including the opponent seat in experimental 9×9. On ordinary
  scenarios it can occupy either seat or both. Keep existing menu defaults
  and preserve the selection when switching between scenarios where it
  remains valid.
- The web client uses the existing `CpuPlayer` for the scripted seat, including
  when reloading a game. Keep the mock player-type catalog aligned with the
  live catalog so the option is visible in mock mode as well.

## Turn behavior

1. When the scripted side is active in Movement, use the existing CPU movement
   command (`POST /games/{gameId}/movement`). It returns the normal movement
   response with `plans: []`, not a missing plan, a fabricated stationary
   move, or an error. No unit moves as a result of the policy.
2. Apply and acknowledge authoritative state through the existing CPU flow.
   If the game is still in progress, finish Movement through the usual
   command. Continue through Combat if the engine finds pending combats;
   otherwise proceed to End Turn. No-op means **no movement orders**, not
   skipping combat or suppressing scoring, victory checks, reinforcements,
   or other normal engine effects.
3. End the turn through the usual command. Hand off to a human or start the
   next CPU turn as appropriate. Stop issuing commands when the game is
   complete. Reuse existing command sequencing, version checks, and replay
   handling; do not advance the browser independently of a failed server
   command or add a scripted-only turn endpoint.

## Acceptance criteria

- A focused policy test instantiates the player without an API or ML runtime,
  verifies repeated calls return no plans even when owned units could move,
  and verifies callbacks do not introduce policy state or unit changes.
- Verify the live player-type catalog and create/load round trip. Exercise
  the scripted type on both seats across at least two different scenarios,
  and verify a saved game restores the scripted behavior, not merely its
  display label. Include the experimental 9×9 opponent seat in coverage.
- Through the normal CPU command path, verify an empty plan response leaves
  unit positions unchanged and that the ordinary phase commands advance to
  the next player. Cover both pending combat and no pending combat, and
  verify no command follows a completed-game response.
- Verify the web picker submits `scripted`, a new or reloaded scripted seat is
  automatically played by the CPU flow, and scripted-versus-scripted hands off
  without waiting for human input. Existing player options remain
  available wherever they were previously supported.

## Out of scope

Unit grouping and objective assignment, pathfinding, holding/support behavior,
tactical decision-making, scenario schema changes, and PPO training integration
belong to later increments. This slice needs no third-party strategy framework
or new game-rule logic.

## Open Questions

No questions.
