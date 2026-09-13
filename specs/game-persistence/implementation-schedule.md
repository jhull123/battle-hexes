---
title: Game Persistence Implementation Specification Schedule
version: 1.0
date_created: 2026-09-13
last_updated: 2026-09-13
tags: [process, game-persistence, api, frontend, dynamodb]
---

# Game Persistence Implementation Specification Schedule

## 1. Purpose

This document divides the game-persistence design into focused implementation
specifications. Each increment should be small enough to implement and verify
independently, but substantial enough to deliver a coherent architectural or
behavioral capability.

The requirements and contracts in [`docs/design.md`](../../docs/design.md) are
authoritative. Each implementation specification created from this schedule
must reference the relevant design sections and resolve implementation details
without weakening those requirements.

## 2. Scheduling Principles

- Follow the dependency order below unless an implementation specification
  documents why work can safely proceed in parallel.
- Keep incomplete infrastructure and adapters unselected at runtime rather than
  exposing partially implemented persistence behavior.
- Do not enforce the new HTTP command contract until the backend and frontend
  are both ready for coordinated activation.
- Run existing tests throughout the work so preparatory increments do not alter
  current game behavior unintentionally.
- Treat the in-memory and DynamoDB repositories as implementations of one
  observable contract, not as production and test variants with different
  semantics.
- Do not modify `battle_hexes_core` as part of these increments.
- Do not introduce a production shadow-write path. An inactive DynamoDB adapter
  exercised through contract and integration tests provides safer validation
  without temporary dual-write semantics or contamination of authoritative
  keys.

## 3. Implementation Increments

### 3.1 Persistence Contracts and Command Identity

**Objective:** Establish API-owned persistence vocabulary and deterministic
command identity without changing route behavior.

**Scope:**

- Define the `GameRepository` interface and storage-neutral persistence types,
  results, and errors described in the design.
- Define stored game metadata, command identity, completed command receipts,
  game versions, timestamps, and expiry metadata.
- Implement idempotency-key validation and hashing.
- Implement canonical request fingerprinting from the method, normalized route,
  expected version, and validated request body.
- Establish injectable clock and encoded-item-budget interfaces or utilities
  needed by both repository implementations.
- Do not require new headers from live routes in this increment.

**Completion evidence:** Unit tests demonstrate stable fingerprints, key
privacy, validation boundaries, storage-neutral errors, and deterministic time
and size behavior.

**Dependencies:** None.

### 3.2 Game-State Codec

**Objective:** Serialize and hydrate a complete authoritative game independently
of any storage implementation.

**Scope:**

- Define state schema version 1 and its API-owned persistence document.
- Serialize all authoritative runtime state identified in the design while
  preserving behaviorally significant ordering and references.
- Rebuild the object graph from the saved document and the matching scenario.
- Detect unsupported state schema versions, missing scenarios, and scenario
  version mismatches.
- Reconstruct supported player types while excluding transient Q-learning state.
- Keep any necessary access to core runtime attributes isolated inside the
  codec.

**Completion evidence:** Round-trip tests cover every scenario and player type,
plus representative movement, combat, defensive-fire, reinforcement, scoring,
and completed-game states. Tests compare observable behavior and authoritative
state rather than only comparing serialized JSON.

**Dependencies:** Increment 3.1.

### 3.3 Contract-Compliant In-Memory Repository

**Objective:** Provide a local repository with the same correctness semantics as
the future DynamoDB adapter.

**Scope:**

- Implement detached loads by passing snapshots through the game-state codec.
- Implement atomic creation and mutation of a game and its successful receipt.
- Enforce optimistic versions, logical expiry, idempotency conflicts, and state
  and receipt size budgets.
- Use an injectable clock and synchronization suitable for concurrent local
  requests.
- Guarantee that command, serialization, or commit failure leaves the previous
  state authoritative.
- Create a reusable repository contract suite intended for both repository
  adapters.
- Keep existing routes on their current persistence path until activation.

**Completion evidence:** The contract suite verifies detached objects,
successful commits, rollback, races, retries, key reuse, exact TTL boundaries,
and capacity rejection.

**Dependencies:** Increments 3.1 and 3.2.

### 3.4 Command Service Foundation

**Objective:** Implement storage-independent orchestration for one authoritative
game command without yet changing live routes.

**Scope:**

- Implement receipt lookup before game loading and version validation.
- Implement create and existing-game command flows, including expected-version
  comparison and exactly-one version advancement after a successful commit.
- Capture the finalized successful status, exact body bytes, content type,
  application-controlled headers, and resulting game version before commit.
- Replay matching receipts and reject mismatched idempotency-key reuse without
  invoking game behavior.
- Translate repository outcomes into the structured API errors defined by the
  design.
- Define how ambiguous or competing commit results are resolved through receipt
  and game reloads.

**Completion evidence:** Service-level tests use the in-memory repository to
verify successful creation and mutation, exact replay, stale writes, validation
ordering, failed-command key reuse, and unresolved commit handling.

**Dependencies:** Increments 3.1 through 3.3.

### 3.5 Game Command Adapters

**Objective:** Make every state-affecting route behavior executable through the
command service while keeping route activation as a separate decision.

**Scope:**

- Adapt game creation and all existing movement, combat, and end-turn POST
  behaviors to the command service.
- Move persistence orchestration out of route functions while retaining the
  existing successful response shapes.
- Ensure synchronous state-affecting callbacks run before snapshot and response
  serialization.
- Ensure every state projection in one response reports the same resulting game
  version.
- Preserve random combat outcomes through receipt replay without rerunning game
  logic.
- Keep schema code limited to validation, serialization, and conversion of
  already-computed core results.

**Completion evidence:** Adapter and service tests cover all POST routes,
including no-visible-change commands, callbacks, reinforcement, scoring,
terminal states, and random combat replay.

**Dependencies:** Increment 3.4.

### 3.6 Frontend Persistence Protocol

**Objective:** Prepare the web application to obey the versioned and idempotent
HTTP command contract when it is activated.

**Scope:**

- Retain the authoritative `gameVersion` from create, load, and command
  responses.
- Generate one idempotency key for each logical POST and retain the same key,
  route, body, and expected version for retries.
- Send `Expected-Game-Version` for commands against existing games.
- Serialize commands per game and prevent duplicate user or CPU submission
  while a command is in flight.
- Parse structured API errors and recover from a version conflict by loading and
  applying authoritative state rather than resubmitting stale intent.
- Prevent local turn or phase advancement after failed commands.
- Update the frontend mock service to represent the new client-facing contract.

**Completion evidence:** Frontend unit tests verify key reuse, version updates,
command serialization, retry behavior, structured errors, stale-state recovery,
and failure-safe UI state.

**Dependencies:** The HTTP contract in `docs/design.md`; development may proceed
in parallel with increments 3.4 and 3.5.

### 3.7 In-Memory End-to-End Activation

**Objective:** Activate the complete persistence command contract using the new
in-memory repository before introducing DynamoDB as an operational dependency.

**Scope:**

- Select and inject the in-memory repository and command service through the
  FastAPI application lifespan and application state.
- Migrate all game GET and POST routes together and remove API use of
  module-global mutable game state.
- Enforce `Idempotency-Key` and `Expected-Game-Version` as designed.
- Expose version fields and `Game-Version`, configure CORS exposure, and return
  the specified structured errors.
- Exercise complete browser-to-API game flows using detached snapshots.
- Coordinate release of this activation with the frontend protocol changes.

**Completion evidence:** API and frontend suites pass against the in-memory
adapter, and route tests demonstrate versioning, replay, detached requests,
conflicts, expiry, and stable response shapes across every game command.

**Dependencies:** Increments 3.3 through 3.6.

### 3.8 DynamoDB Repository

**Objective:** Implement a fully contract-compliant DynamoDB adapter while
leaving runtime repository selection unchanged.

**Scope:**

- Implement strongly consistent game and receipt reads.
- Implement conditional transactional creation and mutation of game snapshots
  and receipts.
- Enforce optimistic versions, logical expiry, replaceable expired records, and
  pre-transaction item-size budgets.
- Translate DynamoDB errors and transaction cancellation outcomes into
  storage-neutral repository results.
- Resolve condition races and ambiguous outcomes using strongly consistent
  receipt and game reads as required by the design.
- Avoid scans, queries, indexes, streams, and non-transactional game/receipt
  writes.

**Completion evidence:** The shared repository contract suite passes against a
DynamoDB-compatible service or disposable table. Additional tests verify AWS
request construction, transaction races, concurrent identical commands,
ambiguous results, and physically present expired items.

**Dependencies:** Increments 3.1 through 3.3. It may be developed in parallel
with command and frontend work after those foundations exist.

### 3.9 Infrastructure and Readiness Preparation

**Objective:** Prepare deployed infrastructure and startup validation before the
DynamoDB adapter becomes authoritative.

**Scope:**

- Verify table activity, string `pk`/`sk` key schema, and TTL enabled on `ttl`.
- Add only the IAM permissions required by repository operations and readiness,
  including `DescribeTimeToLive`.
- Validate table-name and enabled-mode configuration and define startup failure
  behavior without silent in-memory fallback.
- Keep `/health` independent of AWS and preserve in-memory readiness without AWS
  access.
- Keep CloudFormation templates and their canonical lint script synchronized.

**Completion evidence:** Readiness tests cover inactive or unavailable tables,
wrong key schemas, disabled TTL, missing configuration, and in-memory mode.
CloudFormation checks pass.

**Dependencies:** The data and configuration contracts in `docs/design.md` and
increment 3.8's concrete access requirements.

### 3.10 DynamoDB Cutover and Operational Hardening

**Objective:** Make DynamoDB authoritative in enabled environments and verify
the complete production failure model.

**Scope:**

- Select the DynamoDB repository once during lifespan initialization when
  `DYNAMODB_ENABLED=true`; select memory only when explicitly disabled.
- Return success only after the snapshot and receipt are durably committed.
- Add telemetry for repository operations, latency, versions, conflicts,
  replays, expiry, item sizes, and categorized DynamoDB failures without logging
  sensitive payloads or raw keys.
- Validate restart persistence, cross-instance visibility, concurrency,
  ambiguous-result recovery, logical TTL, and near-budget history growth.
- Document deployment verification and rollback conditions for the coordinated
  backend configuration change.

**Completion evidence:** Integration tests and deployment checks demonstrate
authoritative cross-process behavior, exactly one committed result under races,
successful retry after a lost response, and no fallback during DynamoDB
failure. All server, frontend, infrastructure, and repository checks pass.

**Dependencies:** Increments 3.7 through 3.9.

## 4. Activation Boundaries

The schedule contains two notable release boundaries:

| Boundary | Included increments | Required coordination |
| --- | --- | --- |
| Versioned in-memory activation | 3.1-3.7 | Backend and frontend must ship together because all POST headers become mandatory. |
| DynamoDB authority | 3.8-3.10 | Infrastructure, readiness, integration coverage, and operational visibility must be ready before enabled environments select DynamoDB. |

Preparatory increments may be merged independently when they leave current
runtime selection and HTTP behavior unchanged. Passing unit tests for an
inactive component is not sufficient evidence to cross an activation boundary.

## 5. Requirements for Each Implementation Specification

Each implementation specification derived from this schedule must include:

- the increment objective and explicit in-scope and out-of-scope behavior;
- references to the applicable sections of `docs/design.md`;
- affected projects and expected component boundaries;
- public and internal contracts introduced or changed;
- implementation sequencing and runtime activation impact;
- observable acceptance criteria and automated test coverage;
- failure, concurrency, expiry, and rollback considerations where applicable;
- dependencies on earlier increments and any work that may proceed in parallel;
  and
- an `Open Questions` section containing only decisions required before that
  increment can be implemented.

## Open Questions

No questions.
