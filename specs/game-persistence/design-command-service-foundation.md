---
title: Command Service Foundation
version: 1.0
date_created: 2026-09-19
last_updated: 2026-09-19
tags: [design, game-persistence, api, command-service, idempotency]
---

# Introduction

This specification defines increment 3.4 of the game-persistence schedule: a
storage-independent service that executes one authoritative game command and
returns a durable, exactly replayable response.

## 1. Purpose & Scope

Implement the API command-service orchestration shared by game creation and
commands against existing games. The service validates persistence preconditions,
checks receipts before game state, executes injected game behavior on detached
state, finalizes the response and snapshot, and atomically commits both through
`GameRepository`.

This increment uses the in-memory repository in service tests only. It does not
change live routes, enforce headers at the HTTP boundary, implement individual
route adapters, select a runtime repository, or modify `battle_hexes_core`.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Command handler | Injected callable that performs one domain operation on a newly created or detached game and returns data needed to form its successful response. |
| Finalized response | Immutable status, exact body bytes, content type, application-controlled headers, and resulting game version. |
| Replay | Returning the response stored in a matching, unexpired receipt without loading a game or invoking a handler. |
| Reconciliation | Authoritative receipt and game reads used to classify a failed, competing, or ambiguous commit. |
| Existing-game command | A command whose aggregate exists before execution and therefore requires an expected version. |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Add an API-owned `GameCommandService` that depends only on the
  `GameRepository`, `GameStateCodec`, `Clock`, command-identity utilities, and
  injected callables. It must not depend on FastAPI request/response objects or
  a concrete repository.
- **REQ-002**: Provide separate creation and existing-game entry points. Inputs
  must already contain a validated idempotency key, normalized route, validated
  API body, and, for existing games, a positive expected version.
- **REQ-003**: Each entry point must calculate `CommandIdentity` and call
  `find_receipt` before creating or loading a game, comparing a game version, or
  invoking a command handler.
- **REQ-004**: A matching receipt must immediately produce an exact replay. A
  receipt with the same key digest and a different fingerprint must raise the
  structured `409 idempotencyKeyReused` error. Neither path may invoke game
  behavior, decoding, response serialization, or a write.
- **REQ-005**: Creation must build a detached game, assign persistence metadata,
  encode version 1, finalize a version-1 response, and call `create_game` once.
- **REQ-006**: An existing-game command must load and decode a detached snapshot,
  compare its current version with the expected version, and reject a mismatch
  before invoking the handler. A successful unique command must encode and
  commit exactly version `N + 1` with `expected_version=N`.
- **REQ-007**: Every accepted unique existing-game command advances the version
  exactly once, including a command with no visible state change. Failed and
  replayed commands do not advance it.
- **REQ-008**: The handler and all synchronous state-affecting callbacks must
  finish before state encoding and response finalization. A handler, callback,
  codec, or serializer failure must not call a repository commit.
- **REQ-009**: Before commit, construct the complete `StoredGame` and immutable
  `CommandReceipt`. The receipt must capture the successful status, exact body
  bytes, content type, application-controlled headers, identity, game ID,
  resulting version, creation time, and fixed expiry.
- **REQ-010**: The response serializer must run exactly once for a unique
  execution. Its output must already contain the resulting camel-case
  `gameVersion` wherever the route response projects game state. The service
  must add or verify `Game-Version` with the same decimal value.
- **REQ-011**: Only application-controlled headers are persisted. Header names
  must be compared case-insensitively, stored in one canonical form, and exclude
  transport-generated headers such as `Date`, `Server`, and `Content-Length`.
  `Content-Type` is stored explicitly and returned identically on replay.
- **REQ-012**: Use one `clock.now()` value to derive all timestamps for a commit.
  Successful mutation applies the configured sliding game expiry and a 24-hour
  receipt expiry. Lookup and replay do not refresh either expiry.
- **REQ-013**: Treat the receipt returned by `create_game` or `commit_command` as
  authoritative. This may be the candidate receipt or a matching receipt won by
  a concurrent request; always return the response represented by that receipt.
- **REQ-014**: On any competing or potentially ambiguous commit outcome, reconcile
  without rerunning the handler: read the receipt first, then conditionally read
  the game as specified in section 4.4. Reconciliation reads must be bounded.
- **REQ-015**: Translate storage-neutral failures into the error contract in
  section 4.5. Preserve known expected/current versions. Do not expose exception
  text, provider metadata, snapshots, response bodies, or raw idempotency keys.
- **REQ-016**: An unsuccessful command never creates a receipt. The same key may
  be reused after validation, not-found, stale-version, domain, serialization,
  capacity, or unresolved-persistence failure, subject to a receipt appearing
  later from an ambiguous commit.
- **CON-001**: Command handlers must have no non-transactional external side
  effects. The service guarantees one committed transition, not at-most-once
  entry into handler code under concurrency.
- **CON-002**: Schema modules remain limited to validation, serialization, and
  conversion of already-computed results; they must not invoke game evaluators.
- **CON-003**: Do not activate the service in routes or alter current HTTP
  behavior in this increment.

## 4. Interfaces & Data Contracts

### 4.1 Service-facing values

```python
@dataclass(frozen=True)
class SuccessfulResponse:
    status_code: int
    body: bytes
    content_type: str
    headers: Mapping[str, str]
    game_version: int

@dataclass(frozen=True)
class CommandRequest:
    idempotency_key: str
    method: str
    normalized_route: str
    validated_body: Mapping[str, object]
    expected_game_version: int | None
```

Values must be defensively copied. `SuccessfulResponse.body` is the exact byte
sequence sent for both first success and replay; the service must not parse and
re-serialize receipt bodies.

### 4.2 Collaborator contracts

```python
class GameCommandService:
    def create(self, request, create_game, serialize_response) -> SuccessfulResponse: ...
    def execute(self, game_id, request, apply_command, serialize_response) -> SuccessfulResponse: ...
```

`create_game` returns a new core game plus scenario metadata. `apply_command`
mutates only the decoded detached game and returns an operation result.
`serialize_response(game, operation_result, resulting_version)` returns the
successful status, body bytes, content type, and application headers. The codec
encodes the complete authoritative game independently of response serialization.

### 4.3 Required execution order

Creation:

1. Validate service-level invariants and derive identity.
2. Find and handle the receipt.
3. Create the game and metadata; set version 1.
4. Run required synchronous callbacks.
5. Encode state and finalize the successful response and receipt.
6. Atomically create the snapshot and receipt.
7. Return the repository's authoritative receipt as a response.

Existing game:

1. Validate service-level invariants and derive identity.
2. Find and handle the receipt.
3. Load and decode the detached game.
4. Compare expected and current versions.
5. Apply the command and synchronous callbacks.
6. Encode version `N + 1`; finalize the response and receipt.
7. Atomically commit using expected version N.
8. Return the repository's authoritative receipt as a response.

### 4.4 Commit reconciliation

After `GameAlreadyExistsError`, `GameVersionConflictError`, or
`PersistenceUnavailableError` from a commit:

1. Call `find_receipt` once. Replay a matching receipt; translate a different
   fingerprint to `idempotencyKeyReused`.
2. If no receipt exists after creation, do not run creation again. Return
   `gamePersistenceUnavailable`; a present game without its receipt is not
   sufficient proof of a replayable success.
3. If no receipt exists after an existing-game command, call `load_game` once.
   Translate absent/expired state to `gameNotFound`; translate a version other
   than the request's expected version to `gameVersionConflict`; otherwise
   return `gamePersistenceUnavailable` because the commit outcome is unresolved.
4. If either reconciliation read is unavailable or internally inconsistent,
   return `gamePersistenceUnavailable`. Never report the locally computed
   response as successful without an authoritative receipt.

Repositories may already perform stronger internal resolution. The service
still applies this sequence to unresolved storage-neutral results; it performs
no provider-specific inspection or retry loop.

### 4.5 Structured error mapping

| Source/condition | Status | `code` |
| --- | ---: | --- |
| Invalid service request invariant | 400 | `invalidIdempotencyKey` or `invalidExpectedGameVersion` |
| Required expected version absent | 428 | `expectedGameVersionRequired` |
| `IdempotencyConflictError` | 409 | `idempotencyKeyReused` |
| `GameNotFoundError` | 404 | `gameNotFound` |
| `GameVersionConflictError` | 409 | `gameVersionConflict` |
| `SavedGameIncompatibleError` | 409 | `savedGameIncompatible` |
| `PersistenceCapacityError` | 507 | `gamePersistenceCapacityExceeded` |
| Unresolved/unavailable persistence or unclassified repository failure | 503 | `gamePersistenceUnavailable` |

Errors use a framework-neutral value with `status_code`, camel-case `code`,
message, and optional `gameId`, `expectedGameVersion`, and `currentGameVersion`.
Domain-validation errors remain the responsibility of later command adapters
and must pass through without being converted to persistence errors.

## 5. Acceptance Criteria

- **AC-001**: A unique creation commits version 1 and returns bytes, content
  type, headers, and version exactly equal to its stored receipt.
- **AC-002**: A unique existing-game command at version N commits N+1 once;
  another command at N receives a conflict containing current version N+1.
- **AC-003**: A matching retry with stale expected version replays before game
  load and returns byte-for-byte identical output without invoking the handler.
- **AC-004**: Reusing a key with a changed route, body, game ID, or expected
  version returns `idempotencyKeyReused` before loading or invoking behavior.
- **AC-005**: Handler, callback, codec, and response-serialization failures make
  no snapshot or receipt visible, and retry with the same key can execute.
- **AC-006**: A no-visible-change command still commits exactly N+1.
- **AC-007**: When concurrent matching requests compete, both return the one
  authoritative receipt and only one transition is committed.
- **AC-008**: An ambiguous commit with a subsequently visible matching receipt
  replays it; absent receipt plus unchanged game returns 503; absent receipt plus
  advanced game returns a version conflict; no case reruns game behavior.
- **AC-009**: Replay preserves exact non-transport headers and body bytes and
  does not extend game or receipt expiry.
- **AC-010**: Existing route tests pass unchanged and no route imports or
  constructs `GameCommandService`.

## 6. Test Automation Strategy

- Add service-level unit tests using the real in-memory repository, codec test
  fixtures, fixed clock, and spy handlers/serializers.
- Use fault-injecting repository decorators for each commit exception and each
  reconciliation outcome; assert public results and invocation counts.
- Use barriers for competing commands and matching-key races. Use deterministic
  response bytes that would expose accidental re-serialization.
- Cover create/mutate success, exact replay, stale writes, validation ordering,
  failed-command key reuse, no-visible-change advancement, capacity rejection,
  incompatibility, and unresolved commits.
- Run `./server-side-checks.sh`; no new coverage threshold is introduced.

## 7. Rationale & Context

Receipt-first lookup makes a retry independent of the now-stale version it
originally carried. Finalizing state and response before the atomic commit
prevents publishing unreplayable outcomes. Returning only an authoritative
receipt also prevents an ambiguous write from being mistaken for success.

## 8. Dependencies & External Integrations

- **DEP-001**: Increment 3.1 supplies identities, value types, errors, clock,
  and the repository protocol.
- **DEP-002**: Increment 3.2 supplies complete state encoding and hydration.
- **DEP-003**: Increment 3.3 supplies the in-memory adapter and atomic receipt
  return semantics used by service tests.
- **DEP-004**: [`docs/design.md`](../../docs/design.md), sections 1.4-1.8 and
  1.16-1.17, is authoritative where this specification is silent.
- No external service or new runtime dependency is required.

## 9. Examples & Edge Cases

| Situation | Required result |
| --- | --- |
| Matching receipt and missing/expired game | Replay receipt. |
| Different fingerprint and current game | Reject key reuse before game load. |
| Unique key and stale expected version | Conflict; key remains reusable. |
| Random result committed but response connection lost | Retry returns stored bytes; do not reroll. |
| Serializer fails after handler mutation | No commit; detached mutation is discarded. |
| Repository returns an older matching receipt after a race | Return that receipt, not local candidate bytes. |
| Receipt appears during ambiguous-result reconciliation | Replay it as authoritative success. |

## 10. Validation Criteria

Implementation is compliant when every acceptance criterion has an automated
service test, failure tests prove no handler rerun during reconciliation,
concurrency tests terminate without deadlock, server checks pass, and code
search confirms live route behavior is unchanged.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.4.
- [Persistence contracts and command identity](architecture-persistence-contracts-command-identity.md), increment 3.1.
- [Game-state codec](design-game-state-codec.md), increment 3.2.
- [Contract-compliant in-memory repository](design-contract-compliant-in-memory-repository.md), increment 3.3.
- [Application persistence design](../../docs/design.md), sections 1.4-1.17.

## 12. Open Questions

No questions.
