# Completed-Game State Consistency (Implementation Specification)

## 1. Overview

Correct the lifecycle transition at the end of a scenario's final turn so a
completed game is represented as completed everywhere: in the core model, all
API projections, mutation endpoints, and the web client.

For the eight-turn **Crossroads on D-Day** scenario, ending the final player's
turn must leave the game at turn `8`; it must not rotate to Player 1, initialize
a ninth movement phase, or retain pending combat. The completed
`gameStatus`—including winner, winning faction, reason, message, and the scores
used to decide the result—remains authoritative and intact.

This is an implementation specification only. It does not make the described
code changes.

## 2. Goals

- Evaluate turn-limit completion after the final player finishes the final
  allowed turn and before any next-turn initialization occurs.
- Establish one canonical completed-state representation across core and API.
- Reject every gameplay mutation after completion before applying request data
  or invoking rules, scoring, callbacks, or persistence updates.
- Make `gameStatus.state === "completed"` authoritative in the frontend rather
  than inferring continued play from phase, active-player, or turn fields.
- Add regression coverage for the full completion result and immutability.
- Preserve all in-progress turn, movement, combat, scoring, and defensive-fire
  behavior.

## 3. Non-goals

- Do not change scenario turn limits, victory conditions, score calculations,
  or tie-breaking rules.
- Do not change the meaning of a turn: a numbered turn still consists of every
  player receiving their turn in player order.
- Do not redesign the phase system for in-progress games.
- Do not add a new endpoint or require a scenario JSON migration.
- Do not use the frontend's displayed turn cap as a substitute for correcting
  server state.
- Do not repair the two example persisted games in place. Correct future state
  transitions; a separate data migration may normalize already-corrupt stored
  games if production persistence requires it.

## 4. Root cause

The current ordering in `battle_hexes_core/game/game.py` is the direct cause:

1. `Game.end_turn()` calls `next_player()` unconditionally.
2. `next_player()` wraps from the last player to the first player, increments
   `turn_number`, changes `current_player`, resets movement and defensive-fire
   state for that player, and only then calls `update_game_status()`.
3. `GameStatusEvaluator._turn_limit_reached()` considers the turn limit reached
   only when `turn_number > turn_limit`.
4. Control returns to `end_turn()`, which unconditionally sets
   `current_phase = "movement"` and clears combats.

Consequently an eight-turn game can only be recognized as complete after it has
already become turn 9, Player 1 has been selected and reset, and the movement
phase has been initialized. The API schemas faithfully serialize those
internally inconsistent fields. The web model accepts them and may render the
next turn/phase even though it separately recognizes the completed status.

There are two related integrity gaps:

- API mutation routes do not reject an already-completed game before applying
  sparse-board input or executing movement, combat, scoring, phase, or turn
  operations.
- Core mutators do not consistently protect the terminal state, so callers
  outside the HTTP layer can also mutate a completed game.

The fix must change the lifecycle boundary, not merely clamp `turnNumber` or
override fields during serialization.

## 5. Canonical lifecycle semantics

### 5.1 Turn-limit boundary

A finite-limit game completes for the turn-limit rule when all of these are
true:

- the current numbered turn equals the scenario turn limit;
- the current player is the last player in the game's configured player order;
- that player ends their turn; and
- an earlier completion condition has not already ended the game.

Evaluation during movement or combat on the final numbered turn must not end the
game merely because `turn_number == turn_limit`; the last player must still be
allowed to finish that turn. Preserve evaluation of unit-elimination and other
immediate victory conditions at their existing rule-defined points.

For compatibility with legacy/inconsistent in-memory state,
`turn_number > turn_limit` should still evaluate as completed. New transitions,
however, must never create that state.

### 5.2 Ordering at `end_turn`

Refactor `Game.end_turn()` into two explicit branches:

1. Re-evaluate the final, already-scored board state at the turn-end boundary.
2. If this is the last player's turn at the limit, compute and store completion
   **without calling `next_player()`**.
3. Canonicalize terminal fields, return the completed result, and perform no
   movement or defensive-fire reset.
4. Otherwise, advance to the next player using the existing behavior, initialize
   that player's movement phase, clear resolved combat state, and retain an
   in-progress status.

The core evaluator should accept explicit turn-end context (for example,
`evaluate(game, *, final_player_turn_ended=False)`) or expose an equivalently
clear turn-end evaluation method. Do not encode a temporary fake turn number,
increment and roll it back, or make schemas invoke the evaluator. The default
evaluation path used during movement/combat must remain context-free and must
not complete early on turn 8.

`next_player()` should remain an in-progress transition primitive. Its status
evaluation should either be moved to the orchestrating method or be guaranteed
not to perform a second, differently timed evaluation.

### 5.3 Canonical completed fields

Once status becomes completed, expose this state consistently:

| Field | Completed value |
| --- | --- |
| `gameStatus.state` | `"completed"` |
| `turnNumber` | The final allowed turn (`8` for Crossroads on D-Day) |
| `currentPhase` | `null` |
| `activePlayer` | `null` |
| `pendingCombats` | `[]` |

Use `null`, rather than inventing a fourth phase string, because `currentPhase`
describes an actionable phase and the existing sparse-board contract already
models both phase and active player as optional. Keep the players and the
completed status's `winnerPlayerName` separately available; a null active player
does not remove or obscure the winner.

The core may retain the last player in a private/internal historical reference
if needed for callbacks or diagnostics, but public current-player/active-player
state must have no active participant after completion. Prefer making
`current_player` itself `None` after all final evaluation has finished so core
state cannot imply that a player may act. Update `get_current_player()` and
`EndTurnResult.current_player` annotations and all completed-path callers to
handle `None` explicitly.

Terminal canonicalization belongs in one core helper invoked whenever a newly
computed status is completed. It must set the phase and active player to null
and clear pending combats without altering board positions, scores, winner,
winner faction, reason, or message. It must be idempotent.

## 6. Core implementation

### 6.1 Files

- `battle_hexes_core/src/battle_hexes_core/game/game.py`
- `battle_hexes_core/src/battle_hexes_core/scoring/game_status_evaluator.py`
- Add a small domain exception module only if needed to avoid a generic
  `ValueError` (for example, `game/game_completed_error.py`).

### 6.2 Required changes

- Add a focused predicate for the end of the final player's final allowed turn;
  it must safely handle no players and unlimited games.
- Give status evaluation explicit knowledge of the turn-end boundary while
  preserving the legacy `turn_number > turn_limit` fallback.
- In `end_turn()`, evaluate and finalize before player rotation whenever the
  predicate is true.
- On ordinary turn endings, retain the existing player rotation, turn increment
  only when wrapping to the first player, movement reset, defensive-fire
  bookkeeping, and movement-phase initialization.
- Canonicalize any completed result in a single place: `current_player = None`,
  `current_phase = None`, and `pending_combats = []`.
- Make `is_game_over()` authoritative from stored `game_status.state` while
  retaining a safe evaluation path for legacy objects whose status is absent.
- Add defense-in-depth guards to public gameplay mutators:
  `apply_movement_plans()`, `end_movement()`, `end_combat()`, and `end_turn()`.
  A completed game must raise a dedicated, deterministic domain error before
  changing state. Guard `next_player()` as well if it remains publicly callable.
- Ensure a mutation that itself causes immediate completion returns that
  completion normally; only subsequent operations are rejected. Route
  orchestration must not invoke another phase transition after such completion.

Do not put status evaluation in API routes or schema constructors. Core remains
the owner of victory rules and evaluation timing.

## 7. API implementation and contract

### 7.1 Mutation rejection

Add one small API guard/helper in an orchestration module (not schema code) and
call it immediately after `_get_game_or_404()` in all gameplay mutation routes:

- `POST /games/{game_id}/movement`
- `POST /games/{game_id}/move`
- `POST /games/{game_id}/end-movement`
- `POST /games/{game_id}/combat`
- `POST /games/{game_id}/end-turn`

When `game.get_game_status().state == "completed"`, return HTTP `409 Conflict`
with a stable detail such as `"Game is completed and cannot be modified"`.
The guard must run before:

- sparse-board input is applied or converted to movement plans;
- player movement generation;
- combat resolution;
- objective scoring/recalculation;
- phase/turn mutation;
- repository update; and
- end-game callbacks.

Keep the core exception guard as defense in depth. Map that exception to the
same `409` response in case completion occurs between orchestration checks; do
not convert it into a 500 response.

A rejected request must not invoke `game_repo.update_game()` and must not invoke
`end_game_cb()` again. Capture a serialized state snapshot before each request
in integration tests and assert that a subsequent GET is identical.

### 7.2 Completion during a request

If movement/defensive fire or combat causes immediate completion within an
otherwise valid request, return the normal successful response containing the
completed status and canonical fields. The route must skip any later phase
transition that would overwrite terminal fields. Persist the completed state
and invoke end-game callbacks according to the existing callback policy.

### 7.3 Schema compatibility change

Update every response projection that carries these fields:

- `GameModel.active_player`: `str | None`
- `GameModel.current_phase`: `str | None`
- `MovementResponseModel.active_player`: `str | None`
- `MovementResponseModel.current_phase`: `str | None`
- `SparseBoard` already declares both values optional; remove its fallback from
  a non-string phase to `"movement"`.

Serialization must derive these values from canonical core state and emit JSON
`null` when completed. It must not call `get_current_player().name` without a
null check. In-progress response shapes and camelCase aliases remain unchanged.

This is a deliberate, narrow API contract widening: clients that previously
assumed both fields were always strings must accept null for completed games.
It is preferable to reporting a fictitious actor or phase. Document this in the
API README or response-model documentation as part of implementation.

The end-turn logger must also tolerate `EndTurnResult.current_player is None`
and log completion rather than interpolating the next player's name.

## 8. Frontend implementation

### 8.1 Authoritative completed state

In `battle-hexes-web/src/model/game.js`, apply the response's `gameStatus`
before interpreting phase and active-player fields, or normalize all fields in
one atomic update. When the status is completed:

- retain the final `turnNumber` from the API;
- expose no actionable current phase;
- expose no active player (extend `Players.setCurrentPlayer()` to accept null,
  or represent the absence explicitly in `Game`);
- clear pending combats; and
- never locally call `endPhase()`, rotate players, increment the turn, or reset
  movement/defensive fire.

`isGameOver()` remains based solely on
`gameStatus.state === "completed"`. Do not infer completion from null fields,
turn-limit arithmetic, winner fields, or message text. Conversely, if this
status is completed, stale non-null `activePlayer`/`currentPhase` values from a
legacy response must not make the UI actionable.

### 8.2 Rendering and automation

Update `menu.js`, `cpu-player.js`, and initial play/startup code as necessary so
completed games:

- display the final turn as `Turn 8 / 8` and never `Turn 9`;
- display `Completed` (or an equivalent non-actionable label) for current turn
  and phase instead of Player 1 / Movement;
- show no current-player highlight or `Turn` badge;
- show no phase as `current-phase`;
- disable the end-phase button and avoid calling `.toLowerCase()`, `.isHuman()`,
  `.getName()`, or `.play()` on null completed-state values;
- do not generate CPU movement, resolve combat, end movement, or end a turn;
  and
- continue to open/render the game-over dialog from the authoritative backend
  status, including winner and reason details.

Remove reliance on `Math.min(turnNumber, turnLimit)` as a correctness workaround.
It may remain as harmless defensive formatting for legacy data only if tests
also prove the model stores and displays the authoritative final turn.

The frontend's existing local guards remain useful for responsiveness, but the
API rejection is the security/integrity boundary.

## 9. Test plan

### 9.1 Core regression tests

Extend `battle_hexes_core/tests/game/test_game.py` and
`battle_hexes_core/tests/scoring/test_game_status_evaluator.py` with observable
behavior tests that:

- construct a two-player finite game at the final numbered turn with the last
  player active, end that player's turn, and assert completion occurs without
  calling/observing a next-player transition;
- assert `turn_number == turn_limit`, `current_phase is None`,
  `get_current_player() is None`, and `pending_combats == []`;
- assert the exact pre-completion scores are unchanged and the resulting winner,
  `winner_player_name`, `winner_faction_id`, reason, and message remain intact;
- cover a score winner and a draw (including the existing reason convention for
  draws), plus objective-control reason where applicable;
- prove ending an earlier player's turn on the final numbered turn remains
  in-progress and advances normally;
- prove unlimited games and non-final turns retain existing behavior;
- prove legacy `turn_number > turn_limit` state still evaluates completed;
- seed pending combats before final completion and assert none remain; and
- parameterize the public core mutators to assert each rejects a completed game
  and leaves a deep/serialized snapshot unchanged.

Tests must assert public state and results rather than private helper calls.

### 9.2 API tests

Extend `battle_hexes_api/tests/test_main.py`, `test_schemas.py`, and/or
`test_schemas_board.py` to verify:

- final-player `end-turn` returns HTTP 200 with `turnNumber: 8`,
  `activePlayer: null`, `currentPhase: null`, `pendingCombats: []`, and a full
  completed `gameStatus`;
- winner player, winning faction, reason, message, and scores survive all
  relevant response projections;
- GET of the completed game returns the same canonical values;
- each of the five mutation endpoints returns HTTP 409 for the same completed
  fixture;
- malicious/different sparse-board input on those rejected requests cannot
  change unit coordinates, movement points, scores, status, phase, combat list,
  or turn number;
- rejected requests do not call movement/combat/scoring functions, repository
  update, or end-game callbacks; and
- schemas serialize null completed fields while preserving string fields for an
  in-progress game.

Prefer one real game/repository integration fixture for the immutability proof,
supplemented by focused mocks only where verifying that downstream services are
not called.

### 9.3 Frontend tests

Extend `battle-hexes-web/tests/model/game.test.js`,
`tests/menu/menu.test.js`, `tests/player/cpu-player.test.js`, and creator/loading
tests as appropriate:

- applying a response with completed status, turn 8, and null phase/player
  produces a completed, non-actionable model without locally incrementing the
  turn;
- completed status overrides stale legacy values (`turnNumber: 9`,
  `activePlayer: "Player 1"`, `currentPhase: "movement"`) for action and phase
  display, while showing the scenario limit rather than “Turn 9”;
- menu rendering shows Completed, no active phase, no current-player badge, and
  a disabled action button without null dereferences;
- neither human phase handling nor recursive CPU play calls any gameplay
  service after completion;
- pending combat is false after completion; and
- winner/faction/reason/score data still reaches the game-over presentation.

Update the completed mock response to use the canonical terminal fields so
offline/manual frontend behavior exercises the new contract.

## 10. Verification commands

From the repository root:

```bash
./server-side-checks.sh
cd battle-hexes-web && npm run test-and-build
```

Focused commands may be used during development, but both full commands must
pass before the implementation PR is opened. End-to-end browser tests are not
required by repository policy.

## 11. Compatibility and rollout

- **Intentional response widening:** `activePlayer` and `currentPhase` become
  nullable only for completed games. This requires synchronized backend and
  frontend deployment (or frontend-first deployment with legacy completed-state
  normalization).
- **Unchanged in-progress contract:** both values remain strings for active
  games; field names, casing, endpoints, and success response envelopes do not
  change.
- **New mutation response:** clients receive HTTP 409 rather than a misleading
  success when mutating a completed game. Treat 409 as terminal and refresh or
  display the already-known game-over state; do not retry.
- **Legacy completed records:** serialization may defensively normalize their
  active player/phase and cap the reported turn at the configured limit, but
  that compatibility projection must not mutate history or replace the fixed
  lifecycle ordering for new games. If persisted objects are durable across
  deployments, implement and separately test a one-time normalization/migration.
- **Callbacks:** ensure the end-game callback occurs once on transition, not on
  later rejected requests. If callback idempotency is not currently tracked,
  add a core transition flag rather than relying on repeated `is_game_over()`
  checks.

## 12. Acceptance criteria

- Ending the last player's turn on turn 8 completes Crossroads on D-Day while
  the stored and returned turn remains 8.
- No next player is activated and no movement phase is initialized.
- Completed responses contain `activePlayer: null`, `currentPhase: null`, and
  `pendingCombats: []` in every applicable projection.
- Winner, faction, reason, message, and scores match the final evaluated state.
- All movement, combat, end-movement, and end-turn mutation attempts after
  completion return HTTP 409 and leave game state byte-for-byte/field-for-field
  unchanged.
- The frontend uses completed status as authoritative, displays no active turn
  or phase, never displays Turn 9 for an eight-turn game, and initiates no more
  gameplay requests.
- Existing non-terminal gameplay tests continue to pass.
- Full backend checks and frontend test/lint/build checks pass.

## 13. Expected implementation touch points

The implementation is expected to modify only focused lifecycle, projection,
route, and presentation files, principally:

- `battle_hexes_core/src/battle_hexes_core/game/game.py`
- `battle_hexes_core/src/battle_hexes_core/scoring/game_status_evaluator.py`
- `battle_hexes_api/src/battle_hexes_api/main.py` (or a small route guard module)
- `battle_hexes_api/src/battle_hexes_api/schemas/game_model.py`
- `battle_hexes_api/src/battle_hexes_api/schemas/movement.py`
- `battle_hexes_api/src/battle_hexes_api/schemas/sparseboard.py`
- `battle-hexes-web/src/model/game.js`
- `battle-hexes-web/src/player/player.js`
- `battle-hexes-web/src/player/cpu-player.js`
- `battle-hexes-web/src/menu.js`
- their corresponding core, API, and frontend test modules and completed mock
  response fixture.

Keep `main.py` thin, keep evaluator calls out of API/schema code, and extract
small helpers rather than adding branching-heavy methods.

## Open Questions

No questions.
