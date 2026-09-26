---
title: In-Memory End-to-End Persistence Activation
version: 1.0
date_created: 2026-09-26
last_updated: 2026-09-26
tags: [design, game-persistence, api, frontend, activation]
---

# Introduction

This specification defines increment 3.7 of the game-persistence schedule: the
single release boundary that activates the versioned command protocol across
the FastAPI API and browser client, backed by the contract-compliant in-memory
repository.

## 1. Purpose & Scope

Replace live API use of process-global core game storage with the API-owned
`GameRepositoryInMemory` and route every game POST through
`GameCommandService`. Activate the already-prepared frontend protocol in the
same release so browser requests satisfy the newly mandatory headers.

In scope are `POST /games`, `GET /games/{game_id}`, and all existing-game POST
routes (`/movement`, `/move`, `/end-movement`, `/combat`, and `/end-turn`), plus
application wiring, HTTP error translation, version headers/fields, Cross-Origin
Resource Sharing (CORS), and end-to-end contract tests. Scenario, player-type,
and health routes retain their behavior.

Out of scope are DynamoDB, repository selection by environment, AWS readiness,
new gameplay behavior, core changes, compatibility with clients that omit the
new headers, and changes to successful response shapes beyond persistence
version fields and headers.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Activation | Coordinated switch of live API routes and frontend calls to the persistence protocol. |
| Application state | Objects created once by FastAPI lifespan and stored on `app.state`. |
| Detached snapshot | A hydrated game object that cannot mutate repository state until a successful commit. |
| Command route | Any POST route that creates or changes a game. |
| Replay | Exact successful response restored from a matching command receipt. |
| Logical expiry | A record with `ttl <= now`, treated as absent even if physically retained. |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: FastAPI lifespan must construct one codec, clock, in-memory
  repository, command response finalizer, and command service per application
  instance. Store the repository and service on `app.state`; routes must obtain
  them from the request/application rather than module globals.
- **REQ-002**: Remove API imports and uses of the core `GameRepository` and all
  module-global mutable game storage. Static registries may remain shared only
  if they hold no mutable game state.
- **REQ-003**: All six command routes must use the increment 3.5 adapters and
  serializers through `GameCommandService`. Routes may validate HTTP input,
  assemble `CommandRequest`, invoke the service, and translate its finalized
  result; they must not execute game rules or persist games directly.
- **REQ-004**: `GET /games/{game_id}` must load a detached `StoredGame` from the
  repository and serialize it with its repository `gameVersion` and saved
  `scenarioVersion`. A GET must not create a receipt, increment a version, or
  extend expiry.
- **REQ-005**: Every POST must require and validate `Idempotency-Key`. Every
  existing-game POST must also require and validate
  `Expected-Game-Version`; creation must not require an expected version.
- **REQ-006**: Header validation and request-body validation must occur before
  command execution. A rejected request must not consume its idempotency key or
  change state. Receipt lookup ordering within a valid command remains governed
  by `GameCommandService`.
- **REQ-007**: Convert `SuccessfulResponse` to a raw FastAPI response without
  reserializing its body. Preserve its status, exact bytes, content type, and
  application-controlled headers so initial and replayed responses are
  indistinguishable.
- **REQ-008**: Every successful game GET or POST must include `Game-Version`
  and camel-case `gameVersion`. Full-game projections must include
  `scenarioVersion`; multiple projections in one response must agree.
- **REQ-009**: Map command and repository failures to the structured camel-case
  error contract in section 4.3. Known current/expected versions must be
  included. Domain validation may retain its existing status and detail shape
  where the persistence design does not define a replacement.
- **REQ-010**: CORS must allow `Idempotency-Key` and
  `Expected-Game-Version` and expose `Game-Version`. Existing permitted origins,
  methods, and credentials policy remain unchanged unless separately reviewed.
- **REQ-011**: The frontend must activate increment 3.6 without a legacy
  fallback: create and command calls send stable keys, existing-game commands
  send the retained version, successful results apply the returned version,
  and conflicts reload authoritative state.
- **REQ-012**: A successful unique existing-game command advances the version
  exactly once, including a no-visible-change command. Replay, GET, rejection,
  serialization failure, and commit failure advance it zero times.
- **REQ-013**: The activated repository must retain the configured 24-hour game
  and receipt lifetimes, exact logical-expiry boundary, detached hydration,
  atomic game/receipt commits, and encoded-size limits established in increment
  3.3.
- **CON-001**: This activation always selects `GameRepositoryInMemory`.
  `DYNAMODB_ENABLED` and `DDB_TABLE_NAME` do not select a runtime adapter until
  increments 3.8-3.10.
- **CON-002**: Do not add optional-header grace behavior, dual persistence,
  shadow writes, or retry stale commands with a new expected version.
- **CON-003**: Keep `main.py` thin. Place lifespan composition, HTTP extraction,
  response conversion, and error translation in cohesive API-owned components
  when keeping them in routes would duplicate logic or exceed size guidance.
- **CON-004**: Do not modify `battle_hexes_core` or put orchestration in schema
  modules.

## 4. Interfaces & Data Contracts

### 4.1 Runtime composition

The application exposes these logical state entries for its full lifespan:

```python
app.state.game_repository: GameRepository
app.state.game_command_service: GameCommandService
```

Tests must be able to create an application with an injected clock and/or
repository without mutating module globals. Shutdown performs no persistence
flush; in-memory state belongs to that application instance and is intentionally
lost when the process ends.

### 4.2 Route contract

| Route class | Required request headers | Successful version source |
| --- | --- | --- |
| `POST /games` | `Idempotency-Key` | Created version 1 from service result |
| Existing-game POST | `Idempotency-Key`, `Expected-Game-Version` | Committed/replayed service result |
| `GET /games/{game_id}` | None | Loaded repository metadata |

`Expected-Game-Version` is a positive base-10 integer with no boolean, sign,
fraction, or surrounding-content coercion. `Idempotency-Key` uses the validation
limits defined by increment 3.1. Header names remain case-insensitive per HTTP.

### 4.3 Structured persistence errors

| Condition | Status | `code` |
| --- | --- | --- |
| Missing/invalid idempotency key | 400 | `invalidIdempotencyKey` |
| Missing expected version | 428 | `expectedGameVersionRequired` |
| Invalid expected version | 400 | `invalidExpectedGameVersion` |
| Expected/current version differ | 409 | `gameVersionConflict` |
| Key reused for another fingerprint | 409 | `idempotencyKeyReused` |
| Game absent or logically expired | 404 | `gameNotFound` |
| Saved state/scenario incompatible | 409 | `savedGameIncompatible` |
| Persistence outcome unavailable | 503 | `gamePersistenceUnavailable` |
| Snapshot or receipt over budget | 507 | `gamePersistenceCapacityExceeded` |

Error bodies use the command-service error model and camel-case fields. Error
responses do not include `Game-Version` unless the established error model
explicitly requires it; known versions belong in the JSON error fields.

### 4.4 Successful response boundary

The HTTP adapter must emit `SuccessfulResponse.body` unchanged and apply
`status_code`, `content_type`, and `headers` directly. The adapter must not add
a replay marker, rebuild JSON from a model, run a serializer twice, or save
transport-controlled headers such as `Date`, `Server`, or `Content-Length`.

## 5. Acceptance Criteria

- **AC-001**: Given a fresh application, when a valid create request is sent
  with an idempotency key, then version 1 is returned in JSON and
  `Game-Version`, and a matching retry returns the exact status, body bytes,
  content type, and application headers without creating another game.
- **AC-002**: Given version N, when any existing-game command succeeds, then
  detached state is committed as N+1 and a subsequent GET returns that state,
  N+1 in both version locations, and the saved scenario version where required.
- **AC-003**: Given the same key, route, validated body, and old expected
  version, when a successful command is retried, then the receipt is replayed
  before stale-version evaluation and game logic is not rerun.
- **AC-004**: Given two different commands against version N, when they race,
  then exactly one commits N+1 and the other receives
  `gameVersionConflict`; no partial state or receipt is visible.
- **AC-005**: Missing/malformed headers and every persistence failure produce
  the section 4.3 status/code, do not advance state, and leave an uncommitted
  key reusable.
- **AC-006**: At `ttl == now`, GET and command treat the game as not found.
  GET, rejected requests, and receipt replay do not extend TTL; a unique
  successful command does.
- **AC-007**: Objects loaded for two requests are detached. Mutation or failure
  in one request is invisible to the other unless its atomic commit succeeds.
- **AC-008**: Browser preflight accepts both command headers, and browser code
  can read `Game-Version` from a successful cross-origin response.
- **AC-009**: Frontend flows create, load, move, resolve combat, end movement,
  and end turns using authoritative versions; duplicate submission is blocked,
  retries reuse intent, and a version conflict reloads rather than resubmits.
- **AC-010**: No game route imports or uses the core repository or mutable
  module-global game state, and no command route directly invokes game-rule
  evaluators.

## 6. Test Automation Strategy

- Replace direct route mocks of the core repository with application fixtures
  using a real in-memory repository, codec, deterministic clock, and real
  command service. Mock only external/domain boundaries needed for focused
  response cases.
- Parameterize route-contract coverage across all six POST routes for required
  headers, first success, matching replay, key reuse, stale version, response
  versions, and stable existing body shape.
- Add GET tests for detached loads, missing/expired/incompatible state, version
  fields and header, and no TTL extension.
- Add concurrency tests for different commands and identical keys; assert
  committed state, receipt, invocation count, and response equality rather than
  lock implementation details.
- Add rollback tests for adapter, callback, serialization, capacity, and commit
  failures. Reuse the same key after failures that created no receipt.
- Add CORS preflight and exposed-header tests using the ASGI test client.
- Run `./server-side-checks.sh` and `npm run test-and-build` in
  `battle-hexes-web`. Browser E2E execution is optional per repository guidance;
  API route integration plus frontend service/controller tests are required.

## 7. Implementation Sequence & Activation

1. Add application composition and injectable test construction while leaving
   route behavior unchanged.
2. Add shared request-header parsing, success-response conversion, and
   structured error translation.
3. Migrate GET to detached repository loads and verify non-mutating semantics.
4. Migrate all six POST routes together to command adapters/service; delete the
   core repository global and obsolete route orchestration.
5. Configure CORS and activate frontend protocol behavior in the same release.
6. Run API/frontend suites and release only when all activation criteria pass.

Steps 3-5 may coexist on a development branch but must not be deployed
independently. Rollback is a full backend-and-frontend release rollback; it is
not runtime fallback to the old global repository.

## 8. Dependencies & External Integrations

- **DEP-001**: Increments 3.3-3.5 provide the repository, command service,
  adapters, serializers, and their passing contract suites.
- **DEP-002**: Increment 3.6 provides the prepared frontend persistence
  protocol and mock-service behavior.
- **DEP-003**: [`docs/design.md`](../../docs/design.md), sections 1.4-1.8,
  1.11, 1.13, and 1.15-1.17, is authoritative where this spec is silent.
- No database, AWS service, schema migration, or new runtime package is needed.

## 9. Examples & Edge Cases

| Situation | Required result |
| --- | --- |
| Combat commits but response is lost | Retry returns the stored random outcome without rerunning combat. |
| Matching retry carries version N after game reached N+1 | Replay succeeds because receipt lookup precedes version comparison. |
| Same key is used against another game or route | Return `idempotencyKeyReused`; execute nothing. |
| Serializer fails after detached mutation | Preserve version N and create no receipt. |
| GET returns a game and caller mutates it | Repository state remains unchanged. |
| Process restarts | In-memory games disappear; this is accepted for this increment. |

## 10. Validation Criteria

Implementation is compliant when every game route uses application-state
persistence, route tests cover every AC above, API and frontend checks pass,
code search finds no live use of the core game repository, and the backend and
frontend are releasable as one activation unit.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.7.
- [In-memory repository](design-contract-compliant-in-memory-repository.md).
- [Command service](design-command-service-foundation.md).
- [Command adapters](design-game-command-adapters.md).
- [Frontend protocol](design-frontend-persistence-protocol.md).
- [Application persistence design](../../docs/design.md).

## Open Questions

No questions.
