---
title: Game Command Adapters
version: 1.0
date_created: 2026-09-19
last_updated: 2026-09-19
tags: [design, game-persistence, api, command-adapters]
---

# Introduction

This specification defines increment 3.5 of the game-persistence schedule: thin,
testable adapters that make every state-affecting game behavior executable by
the `GameCommandService` without activating the new HTTP contract.

## 1. Purpose & Scope

Extract game creation, movement, combat, and turn-transition behavior from
FastAPI route functions into API-owned command adapters. Each adapter mutates
only the game supplied by the command service and returns an operation result
that a paired serializer converts into the route's existing success shape.

This increment covers `POST /games` and all existing `POST /games/{game_id}`
commands: `/movement`, `/move`, `/end-movement`, `/combat`, and `/end-turn`. It
does not switch live routes to the command service, enforce command headers,
change GET behavior, select a runtime repository, modify response shapes other
than adding version fields required by the persistence design, or modify
`battle_hexes_core`.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Command adapter | Framework-neutral callable that applies one route's domain workflow to a supplied game. |
| Operation result | Immutable route-specific data needed after mutation to serialize the response. |
| Response serializer | Callable that converts a game, operation result, and resulting version into finalized response input. |
| State-affecting callback | Synchronous player callback whose changes must be included in the committed snapshot. |
| Projection | A representation of game state embedded in a successful response. |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Provide one adapter entry point for creation and one for each of
  the five existing-game POST behaviors. Adapters must not accept FastAPI
  `Request`, `Response`, or dependency objects and must not access a repository.
- **REQ-002**: Creation must validate the scenario, invoke
  `GameCreator.create_sample_game`, and return `CreatedGame` with the scenario
  ID and scenario version required by `GameCommandService.create`.
- **REQ-003**: Existing-game adapters must accept the detached game supplied by
  `GameCommandService.execute`; they must never reload, save, cache, or replace
  that game.
- **REQ-004**: Preserve each current domain workflow and its ordering exactly as
  listed in section 4.2. A completed game must be rejected before applying
  submitted board state or invoking any other game behavior.
- **REQ-005**: Run all synchronous state-affecting callbacks before returning
  from the adapter. If the command leaves the game completed, call every
  player's `end_game_cb` exactly once for that execution. Existing callbacks
  invoked inside core operations, including combat and movement callbacks,
  must remain inside the pre-snapshot execution boundary.
- **REQ-006**: Adapters must return only the minimum operation data required for
  serialization. Movement results retain plans and movement resolution; combat
  retains combat results. Serializers must not rerun game logic, scoring,
  callbacks, or random operations.
- **REQ-007**: Provide paired serializers that preserve the existing successful
  status, content type, and top-level response shape for every route. They must
  emit deterministic JSON bytes through one shared API-model serialization
  utility using client-facing camel-case aliases.
- **REQ-008**: Every game-state projection in one response must expose the same
  supplied `resulting_version` as `gameVersion`. Full-game projections must also
  expose the saved `scenarioVersion`; serializers must not derive either value
  from the core `Game`.
- **REQ-009**: Creation serialization may resolve static scenario display data.
  Existing-command serialization must use the detached game and operation
  result only, except for read-only scenario lookup needed by an existing
  response schema. No serializer may mutate authoritative state.
- **REQ-010**: Domain errors retain their current HTTP status and public detail
  when later translated at the HTTP boundary. Adapter code must not translate
  domain failures into persistence errors or consume an idempotency key.
- **REQ-011**: Adapter and serializer dependencies such as scenario access,
  game creation, combat construction, and scoring must be injectable or
  substitutable in focused tests without patching FastAPI routes.
- **REQ-012**: Random combat resolution occurs only in the combat adapter. A
  receipt replay must bypass both the adapter and serializer, preserving the
  stored result and exact body bytes without another roll.
- **CON-001**: Schema modules remain limited to validation, serialization, and
  conversion of already-computed results; they must not import or invoke
  `Combat`, `ObjectiveScorer`, `GameStatusEvaluator`, or callbacks.
- **CON-002**: Keep `main.py` thin: do not place adapter workflows, response
  assembly helpers, or game-rule evaluators there.
- **CON-003**: Do not wire the adapters into live routes in this increment.
  Existing route tests and behavior must remain unchanged until increment 3.7.
- **GUD-001**: Group cohesive adapters and operation-result types by workflow;
  avoid one oversized service module and avoid one trivial module per function.

## 4. Interfaces & Data Contracts

### 4.1 Service integration

Adapters and serializers must be directly usable with the existing service:

```python
service.create(command_request, create_adapter, create_serializer)
service.execute(
    game_id,
    command_request,
    existing_game_adapter,
    response_serializer,
)
```

`create_adapter()` returns `CreatedGame`. An existing-game adapter has the
logical signature `(game) -> operation_result`. A serializer has the logical
signature `(game, operation_result, resulting_version) -> response parts`
accepted by `GameCommandService`. Request schemas are validated before adapter
invocation and may be captured by an adapter factory or callable object.

Recommended immutable operation results:

```python
@dataclass(frozen=True)
class MovementCommandResult:
    plans: tuple
    movement_resolution: object

@dataclass(frozen=True)
class CombatCommandResult:
    combat_results: object
```

Creation and end-turn need no route-specific result. Results must not contain a
second mutable game reference.

### 4.2 Required adapter workflows

| Adapter | Ordered behavior before completion callbacks |
| --- | --- |
| Create | Confirm scenario exists; create sample game; resolve scenario version; return creation metadata. |
| Movement | Reject completed game; obtain current player plans; apply plans; retain plans and resolution. |
| Human move | Reject completed game; convert submitted sparse board to plans against the current board; apply plans; retain plans and resolution. |
| End movement | Reject completed game; convert and apply submitted plans; award held objectives; end movement; retain plans and resolution. |
| Combat | Reject completed game; apply submitted sparse board; resolve combat once; end combat; award post-combat objective points; recalculate scenario victory; retain combat results. |
| End turn | Reject completed game; apply submitted sparse board; recalculate scenario victory; end turn. Reinforcement deployment and other behavior performed by `game.end_turn()` remains inside this step. |

After the listed behavior, each existing-game adapter invokes completion
callbacks when the resulting game is completed and then returns. Any exception
propagates; the command service consequently performs no commit.

### 4.3 Response matrix

| Command | Existing success body to preserve | Version placement |
| --- | --- | --- |
| Create | `GameModel` | Root `gameVersion`; root `scenarioVersion`. |
| Movement, human move, end movement | `MovementResponseModel` | Root and nested `game.gameVersion`; any additional state projection uses the same value. |
| Combat | `SparseBoard` including scores and combat results | Root `gameVersion`. |
| End turn | `GameModel` | Root `gameVersion`; root `scenarioVersion`. |

All serializers produce status 200 unless an existing route contract says
otherwise, `application/json`, no transport-controlled headers, and valid
UTF-8 JSON bytes. Model-to-JSON conversion uses aliases and stable compact
encoding so the committed receipt is the sole replay source.

## 5. Acceptance Criteria

- **AC-001**: Each command adapter can be passed directly to the appropriate
  `GameCommandService` entry point and commits the expected detached state.
- **AC-002**: Each adapter performs the section 4.2 steps in order and rejects a
  completed game before any submitted state or callback changes it.
- **AC-003**: Movement responses preserve plans, defensive-fire events, scores,
  phase, pending combats, and all existing projections; every projection reports
  the same resulting version.
- **AC-004**: Combat resolves and scores exactly once, serializes the resulting
  combat data, and a matching retry returns identical bytes without another
  adapter, callback, scorer, serializer, or random-number invocation.
- **AC-005**: End movement and end turn preserve objective scoring, phase/turn
  transitions, reinforcement state, terminal state, and existing response
  shapes.
- **AC-006**: Completion callbacks run before codec encoding and response
  serialization. A callback failure leaves no committed snapshot or receipt.
- **AC-007**: A valid no-visible-change command still commits N+1, while any
  adapter or serializer failure commits neither state nor receipt.
- **AC-008**: Scenario-not-found, invalid player configuration, completed-game,
  and invalid submitted-movement failures retain their public domain behavior
  and leave the idempotency key reusable.
- **AC-009**: Schema modules contain no game-rule orchestration, and `main.py`
  contains no newly extracted adapter or serializer implementation.
- **AC-010**: Live route tests pass without routes requiring idempotency or
  expected-version headers and without selecting the new persistence path.

## 6. Test Automation Strategy

- Add parameterized adapter tests for every row in sections 4.2 and 4.3 using
  real domain games where observable behavior matters and spies for ordering.
- Add service-level tests with the in-memory repository and codec for creation,
  every existing POST workflow, no-visible-change execution, domain failure,
  callback failure, serializer failure, and version consistency.
- Use seeded or injected combat randomness to prove first execution is saved;
  retry the same request and assert identical response bytes and unchanged
  invocation counts.
- Cover defensive fire, post-combat scoring, reinforcement arrival, victory and
  turn-limit completion, and completion callbacks with representative games.
- Assert successful response structures semantically. Assert exact bytes only
  for first-success versus receipt-replay equality, not as brittle snapshots.
- Run `./server-side-checks.sh`; no new coverage threshold or end-to-end browser
  test is required for this inactive increment.

## 7. Rationale & Context

Separating domain workflows from HTTP parsing and persistence allows the
command service to execute the same behavior on detached snapshots and to
discard all mutations on failure. Keeping response serialization paired with,
but separate from, mutation ensures random outcomes and callback changes are
captured before the atomic snapshot-and-receipt commit.

## 8. Dependencies & External Integrations

- **DEP-001**: Increment 3.4 supplies `GameCommandService`, `CommandRequest`,
  `CreatedGame`, finalized responses, receipt-first replay, and rollback rules.
- **DEP-002**: Existing core game, combat, scoring, scenario, movement, and
  callback APIs define the domain workflows; this increment does not change
  them.
- **DEP-003**: Existing API schemas define success shapes and camel-case output;
  they require additive persistence-version fields.
- **DEP-004**: [`docs/design.md`](../../docs/design.md), sections 1.4-1.8,
  1.15, and 1.17, is authoritative where this specification is silent.
- No new external service or runtime dependency is required.

## 9. Examples & Edge Cases

| Situation | Required result |
| --- | --- |
| Current player returns no movement plans | Execute and commit N+1 with the normal movement shape. |
| Defensive fire completes the game during movement | Preserve its events; run completion callbacks before snapshot and response serialization. |
| Combat commit succeeds but the connection is lost | Retry replays stored combat bytes and does not roll, score, or callback again. |
| End turn deploys reinforcements | Snapshot and response include deployment before commit. |
| Submitted movement conversion fails | Propagate the domain error; do not mutate, serialize, or commit. |
| Completion callback raises | Discard detached changes; do not create a receipt. |

## 10. Validation Criteria

Implementation is compliant when all six POST behaviors have adapter and
service tests, response-contract assertions prove consistent versions, spy
tests prove callback and replay ordering, server-side checks pass, the document
remains below 300 lines, and code search confirms live routes are not activated.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.5.
- [Command service foundation](design-command-service-foundation.md), increment 3.4.
- [Game-state codec](design-game-state-codec.md), increment 3.2.
- [Application persistence design](../../docs/design.md).

## Open Questions

No questions.
