---
title: Frontend Persistence Protocol
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
tags: [design, game-persistence, frontend, http]
---

# Introduction

This specification defines increment 3.6 of the game-persistence schedule: the
frontend protocol for versioned, idempotent game commands. It prepares the web
application and mock service for coordinated activation with the API in
increment 3.7.

## 1. Purpose & Scope

Add one frontend command boundary that owns game-version tracking, idempotency,
per-game serialization, retry state, and structured API errors. Human and CPU
workflows must apply successful authoritative responses before issuing their
next command and must reconcile version conflicts by loading the game.

This increment covers `POST /games` and all existing-game POSTs (`movement`,
`move`, `end-movement`, `combat`, and `end-turn`), plus successful game GETs.
It does not change backend behavior, persist unfinished commands across page
reloads, automatically replay user intent after a conflict, add offline play,
or modify game rules and API response shapes.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Logical command | One user or CPU intent, including all transport attempts made for it. |
| Command descriptor | Immutable route, serialized body, idempotency key, and expected version retained for a logical command. |
| Retryable failure | A network failure with no usable HTTP response or `503 gamePersistenceUnavailable`. |
| Authoritative state | The latest game representation returned by a successful GET or POST. |
| Reconciliation | Replacing the active frontend game from an authoritative GET after a version conflict. |
| In flight | A logical command that has started and has not succeeded or reached a terminal failure. |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Add `gameVersion` to the frontend `Game` model as a required
  positive integer. Creation/loading must initialize it, successful GET/POST
  application must replace it, and command code must read it through an
  idiomatic getter.
- **REQ-002**: The HTTP service must generate a collision-resistant UUID for
  each new logical POST. UUID generation must be injectable for tests.
- **REQ-003**: Before the first transport attempt, construct one command
  descriptor and serialize its body at most once. Every retry must reuse its
  key, method, route, exact body bytes, and expected version.
- **REQ-004**: Send `Idempotency-Key` on every POST. Send
  `Expected-Game-Version` on every existing-game POST using the version captured
  in the descriptor; never send that header on `POST /games`.
- **REQ-005**: Accept a successful version only when `Game-Version` is a
  positive integer and equals every `gameVersion` projection in the JSON body.
  Treat a missing, invalid, or inconsistent version as a protocol error and do
  not apply the response.
- **REQ-006**: Serialize logical commands per game. A later command for the
  same game may start only after the earlier command succeeds, fails
  terminally, or finishes conflict reconciliation. Commands for different
  games need not share a queue.
- **REQ-007**: Reject or coalesce a duplicate UI action while its command is in
  flight; it must not create another descriptor. Disable the initiating control
  until completion. CPU recursion must use the same serialization boundary.
- **REQ-008**: Automatically retry only retryable failures, with a bounded
  attempt policy. Do not retry validation, domain, capacity, incompatibility,
  not-found, idempotency-reuse, or version-conflict responses.
- **REQ-009**: Parse non-success JSON into a typed `BattleHexesApiError` with
  HTTP status, `code`, public message/detail, and optional `currentGameVersion`
  and `expectedGameVersion`. Malformed/non-JSON failures become protocol errors.
- **REQ-010**: On `gameVersionConflict`, perform one GET after the failed
  command releases its transport attempt, replace the active game with that
  authoritative state, update the URL/configuration as applicable, refresh the
  board and menu, and discard the stale intent. Do not POST it again under a
  new key or version.
- **REQ-011**: Apply a successful response, including its new version, before
  scheduling any next human or CPU command. Response application must remain
  complete before the per-game queue advances.
- **REQ-012**: A failed command must not locally call `Game.endPhase`, switch
  players, start the next CPU phase, animate unconfirmed results, or otherwise
  apply speculative server state. UI controls become usable after terminal
  handling unless the game is completed or reconciliation is still running.
- **REQ-013**: Update `BattleHexesService` and both implementations to the same
  observable contract. The mock must return monotonically increasing versions,
  support deterministic injected errors/retries, and exercise serialization;
  it must not bypass command coordination.
- **CON-001**: Keep HTTP parsing and descriptor retry mechanics in the service
  layer, game-state application in model/orchestration code, and UI disabling
  in presentation code. Do not combine these responsibilities in one module.
- **CON-002**: Do not store idempotency keys in `localStorage`, URLs, logs, or
  game models. Retain a descriptor only for its in-memory retry lifetime.
- **CON-003**: This increment is not independently deployable against the old
  API contract. Merge may occur while inactive, but release must be coordinated
  with increment 3.7.

## 4. Interfaces & Data Contracts

### 4.1 Model and service results

`Game` exposes `get gameVersion()` and updates it only while applying validated
authoritative state. Service methods keep their existing arguments and resolve
with the JSON body after validating the response version; they may attach the
validated version as non-wire result metadata if callers need it before model
construction.

```js
BattleHexesApiError {
  status,
  code,
  message,
  currentGameVersion?,
  expectedGameVersion?
}

CommandDescriptor {
  method: 'POST',
  route,
  bodyText,
  idempotencyKey,
  expectedGameVersion // null only for creation
}
```

API error field names remain camelCase. Error parsing must preserve known
fields without exposing raw response payloads in user-facing output or logs.

### 4.2 Request and response matrix

| Operation | Request version | Successful version source |
| --- | --- | --- |
| Create game | No expected-version header | Header and root body; initializes version 1. |
| Get game | No command headers | Header and root body; replaces tracked version. |
| Existing-game POST | Captured current version in header | Header and all body projections; replaces tracked version. |

All POSTs send `Content-Type: application/json`. A bodyless command retains the
same absence of body on retry rather than alternating between no body and `{}`.

### 4.3 Command lifecycle

1. Enter the per-game queue and mark the initiating action busy.
2. Capture the current version, route, and serialized body; generate one key.
3. Send the descriptor. Retry only under REQ-008 without rebuilding it.
4. On success, validate version consistency and apply the complete response.
5. On version conflict, discard the descriptor and GET/apply authoritative
   state; surface that the attempted action was not applied.
6. On any other terminal failure, preserve the last confirmed local state and
   expose the typed failure.
7. Clear busy state and release the queue only after application or error
   handling completes.

## 5. Acceptance Criteria

- **AC-001**: Given create, load, or command success, the active game retains
  the validated returned version before another command can start.
- **AC-002**: Given a lost response or retryable 503, every attempt has the same
  key, route, exact body text, and expected version; only one UI action exists.
- **AC-003**: Given two commands for one game, the second request is not sent
  until the first response is applied and uses the resulting version.
- **AC-004**: Given simultaneous commands for different game IDs, neither is
  blocked by the other's queue.
- **AC-005**: Given `409 gameVersionConflict`, no automatic POST follows; one
  GET replaces local state/version and the stale action is reported as unapplied.
- **AC-006**: Given any terminal command failure, turn, phase, player, board,
  and CPU scheduling remain at the last confirmed state.
- **AC-007**: Given missing or disagreeing response versions, the client raises
  a protocol error and does not partially apply the body.
- **AC-008**: Human double-clicks and repeated CPU triggers while busy do not
  generate additional keys or HTTP requests.
- **AC-009**: The HTTP and mock services satisfy identical success, failure,
  version, serialization, and busy-state tests.
- **AC-010**: Existing frontend behavior remains intact with versioned fixtures,
  and the production build contains no database client or persistence secret.

## 6. Test Automation Strategy

- Add Jest unit tests around a dedicated command coordinator using injected UUID,
  fetch, and retry policy dependencies; use deferred promises to prove ordering.
- Extend HTTP service tests for all POST headers, body-byte reuse, bodyless POSTs,
  structured errors, version validation, bounded retries, and non-retryable errors.
- Extend model/orchestration tests for create/load version initialization,
  successful response application, human and CPU duplicate suppression, and no
  local phase advancement after failures.
- Test conflict reconciliation with a failed POST followed by one GET and assert
  replacement of board, phase, player, status, and version without another POST.
- Run the same service-contract cases against the mock implementation. Fixtures
  must include `gameVersion`; mock commands advance it exactly once per logical
  success, including retry simulations.
- Run `npm run test-and-build`. Browser end-to-end testing is deferred to the
  coordinated activation increment.

## 7. Rationale & Context

The descriptor makes a retry the same command rather than a second intent. A
per-game queue prevents two browser workflows from racing with one version.
Rejecting inconsistent responses prevents the client from pairing state with
the wrong optimistic-lock value. Reloading after conflicts favors authoritative
state over unsafe automatic replay of possibly obsolete user intent.

## 8. Dependencies & External Integrations

- **DEP-001**: [`docs/design.md`](../../docs/design.md), sections 1.5-1.7,
  1.15-1.17, defines the authoritative HTTP, failure, and test contracts.
- **DEP-002**: Increment 3.5 defines successful command response projections and
  their consistent version fields.
- **DEP-003**: Increment 3.7 activates required headers, CORS exposure of
  `Game-Version`, structured errors, and coordinated browser-to-API behavior.
- **PLT-001**: Use the browser Fetch API and Web Crypto UUID support through
  injectable adapters; add no database or cloud SDK dependency.

Work may proceed in parallel with increments 3.4 and 3.5 against contract
fixtures. Production activation depends on 3.7.

## 9. Examples & Edge Cases

| Situation | Required result |
| --- | --- |
| Create response is lost after commit | Retry the identical creation descriptor; apply replayed version 1. |
| Combat times out | Retain body/key/version; do not reroll locally; retry within policy. |
| 503 exhausts retry limit | Keep confirmed state and descriptor only until terminal handling completes. |
| 507 capacity error | Do not retry automatically or advance phase. |
| Conflict GET also fails | Keep current confirmed state, expose the load failure, and do not resume stale intent. |
| Nested and root versions differ | Reject the whole response as a protocol error. |
| CPU movement succeeds | Apply its version before enqueuing end movement. |
| User navigates to another game | Commands use separate queues; responses must not mutate a different active game. |

## 10. Validation Criteria

Implementation is compliant when every POST uses an immutable descriptor,
service and workflow tests cover the acceptance criteria, all mock fixtures
carry valid versions, `npm run test-and-build` passes, and release notes mark
the change for coordinated activation with increment 3.7.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.6.
- [Game command adapters](design-game-command-adapters.md), increment 3.5.
- [Command service foundation](design-command-service-foundation.md), increment 3.4.
- [Application persistence design](../../docs/design.md).

## Open Questions

No questions.
