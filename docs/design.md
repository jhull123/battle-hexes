# Battle Hexes Application Design

Status: Initial design

Last updated: 2026-09-12

This is a living description of the Battle Hexes application architecture. It
records cross-cutting design decisions that implementation specifications must
follow. The first design area is authoritative game-state persistence.

## 1. Game-State Persistence

### 1.1 Context

The API currently stores live core `Game` objects in a module-global, in-memory
repository. A game belongs to one API process, disappears when that process
stops, and is not visible to another API task. The repository also returns the
stored mutable object itself, so state can change before an explicit save.

Deployed API instances must instead be stateless. DynamoDB is the authoritative
source of game state in a deployed environment. An API instance loads a fresh
game aggregate for a request, executes one command, and commits the resulting
state before returning success. The initial design does not permit a cache to
replace strongly consistent reads. Any future caching design must preserve this
consistency contract or explicitly replace it with a newly agreed contract; a
cache must never become authoritative.

Local development and unit tests use an in-memory implementation with the same
observable behavior as DynamoDB. In particular, the in-memory repository must
return detached games and enforce version, expiry, atomicity, and idempotency
rules. It must not preserve the current shared-object behavior.

### 1.2 Goals

- Keep all persistence abstractions, codecs, DynamoDB code, and boto imports in
  `battle_hexes_api`.
- Make the API application depend on a repository interface rather than a
  storage implementation.
- Keep `battle_hexes_core` unaware of repositories, databases, DynamoDB, boto,
  HTTP versions, and idempotency.
- Treat DynamoDB as authoritative across restarts, deployments, and concurrent
  API tasks.
- Store every game with a monotonically increasing game version.
- Reject stale writes instead of overwriting a newer game state.
- Replay the original successful response when a POST is retried with the same
  idempotency key.
- Persist enough state to continue a game without depending on a previous API
  process.
- Remove inactive game and idempotency data after approximately 24 hours.
- Keep the initial data model simple enough for the current game and history
  sizes while detecting DynamoDB item-size risk before data is lost.

### 1.3 Non-Goals

- No changes to `battle_hexes_core` are part of this work.
- Caching is not part of the initial implementation.
- Authentication, game ownership, and authorization are out of scope. A game
  UUID remains a bearer capability until a separate access-control design is
  created.
- The design does not make old games survive arbitrary scenario or application
  model changes. Scenario and persistence schema versions make incompatibility
  detectable; no migration framework is required initially.
- The initial design does not split game history into separate items or provide
  history pagination.
- Q-learning tables, training progress, and transient agent decisions are not
  authoritative game state and are not persisted.
- Model storage, versioning, training, and deployment for future agents such as
  PPO or AlphaZero are out of scope until those agents are designed.
- DynamoDB Streams are not required.

### 1.4 Component Boundaries

The dependency direction is:

```text
FastAPI route
    -> API game command service
        -> API GameRepository interface
            -> GameRepositoryDynamoDB
            -> GameRepositoryInMemory
        -> API GameStateCodec
            -> core and agent domain objects
```

The API game command service owns request orchestration: idempotency lookup,
strongly consistent game loading, expected-version validation, invocation of
core operations, API response serialization, and atomic commit. FastAPI routes
remain thin and obtain this service through an application dependency.

The `GameRepository` interface and both implementations live in
`battle_hexes_api`. The API stops importing or using the current concrete
repository from `battle_hexes_core`; that core class can remain unchanged for
existing core tests or other core-only use.

The repository interface deals in API persistence types such as a
`StoredGame`, `CommandIdentity`, and `CommandReceipt`. It does not add
persistence fields or methods to core `Game`.

The repository must support these logical operations:

| Operation | Required behavior |
| --- | --- |
| Load game | Return a detached game, metadata, and current version, or report not found/expired/incompatible. |
| Find receipt | Return an unexpired completed command receipt using a strongly consistent lookup. |
| Create game | Atomically create version 1 and its successful command receipt. |
| Commit command | Atomically replace version N with N+1 and create its successful command receipt, conditional on version N. |

Repository errors use storage-neutral API exceptions or result types. Routes
must not inspect boto exceptions or DynamoDB cancellation reason structures.

Repository selection occurs once during FastAPI lifespan initialization. The
selected repository is stored on application state and injected into the game
command service. Module-global mutable game state is removed.

### 1.5 Version Model

Three independent versions have different purposes:

| Version | Purpose |
| --- | --- |
| `gameVersion` | Optimistic concurrency version for one game. Starts at 1 and increases by exactly one for each successfully committed POST affecting that game. |
| `scenarioVersion` | Version from the scenario JSON used to create the game. It identifies the static scenario definition expected by the saved state. |
| `stateSchemaVersion` | Version of the API-owned persistence document format. It allows the codec to reject an unsupported document rather than misreading it. |

Only `gameVersion` participates in optimistic locking. It is repository
metadata and is not added to the core `Game` class.

`scenarioVersion` is read from the validated scenario source when a game is
created and is saved with the game. The API persistence component uses the
existing core `load_scenario_data` function to read `ScenarioData.version`;
version is not added to the core `Scenario` or `Game` classes. On load, the
codec reloads the scenario by ID and verifies the version. A missing scenario
or version mismatch makes the saved game incompatible. The API fails the load
clearly and does not attempt a best-effort conversion. Editing a scenario
without supporting existing saved games is acceptable for this project;
scenario authors must increment the scenario version when compatibility
changes.

`stateSchemaVersion` starts at 1. The initial implementation may reject other
versions without providing migrations.

### 1.6 HTTP Command Contract

Every POST requires an `Idempotency-Key` header. The key is an opaque,
client-generated identifier for one logical action; a UUID is recommended. A
retry must reuse the same key, route, request body, and expected game version.
A different logical action must use a new key.

Every POST against an existing game also requires:

```http
Expected-Game-Version: 7
```

`POST /games` has no existing aggregate to lock and therefore does not require
an expected version. A successful creation produces game version 1.

All successful game GET and POST responses expose the authoritative resulting
version as:

```http
Game-Version: 8
```

and a camel-case `gameVersion` JSON field. Full game responses also expose the
saved `scenarioVersion`. Existing response shapes remain in place rather than
adding a new envelope. Where a response contains more than one game-state
projection, all copies of `gameVersion` must agree.

The initial HTTP status and response body for a successfully executed route can
remain otherwise unchanged. Exact status, body bytes, content type, game
version, and all application-controlled headers are saved in the command
receipt. Transport headers generated by the ASGI server or load balancer, such
as `Date`, are outside the replay contract.

The principal new error contracts are:

| Condition | HTTP status | Code |
| --- | --- | --- |
| Missing or invalid idempotency key | 400 | `invalidIdempotencyKey` |
| Missing expected version on an existing-game POST | 428 | `expectedGameVersionRequired` |
| Invalid expected version | 400 | `invalidExpectedGameVersion` |
| Expected version differs from current version | 409 | `gameVersionConflict` |
| Idempotency key reused for a different command | 409 | `idempotencyKeyReused` |
| Game is logically expired or absent | 404 | `gameNotFound` |
| Saved state or scenario version is unsupported | 409 | `savedGameIncompatible` |
| DynamoDB is unavailable or a commit result is unresolved | 503 | `gamePersistenceUnavailable` |
| Snapshot or receipt exceeds the safe item budget | 507 | `gamePersistenceCapacityExceeded` |

Error bodies use camelCase fields and include current and expected game versions
when known. Version conflicts are not retried automatically with a new version.
The client must load the authoritative game and reconsider the action.

CORS configuration must allow the command headers and expose `Game-Version` to
browser code.

### 1.7 Idempotency Semantics

Idempotency lookup happens before game loading and version comparison. This
ordering is essential: a valid retry carries the old expected version from
before the original commit and must replay successfully rather than fail as
stale.

A canonical request fingerprint includes:

- HTTP method;
- normalized route, including the game ID when present;
- expected game version when present; and
- canonical JSON for the validated request body.

The raw idempotency key is not stored. Its SHA-256 digest identifies the receipt
item. Keys are service-wide because there is currently no authenticated user to
provide a narrower scope.

When an unexpired receipt exists:

- A matching fingerprint returns the exact stored successful status, body, and
  application-controlled headers. The replay adds no marker or other
  observable application-level difference.
- A different fingerprint returns `409 idempotencyKeyReused`.
- No game logic, random combat resolution, scoring, callbacks, or game write is
  performed.

Only successful responses whose game state was atomically committed are stored
as completed receipts. Header, schema, domain-validation, not-found, stale
version, and other unsuccessful responses do not consume an idempotency key.

The guarantee is one committed transition and one replayable outcome, not that
application code can never begin twice. Two simultaneous first requests can
both compute on detached state, but DynamoDB permits only one transaction to
commit. The losing request reads and replays the winning receipt. Command
execution must therefore have no non-transactional external side effects.
Current state-affecting player callbacks execute before snapshot serialization
and are included in the committed state. A future callback that sends messages
or writes another system will require an outbox design.

This guarantees that a combat request which commits and then loses its network
connection returns the original combat result when retried. The CRT is not
authoritatively rerolled and the game is not advanced twice.

The idempotency guarantee lasts 24 hours from the successful command. Receipt
replay does not extend either the receipt or the game expiry.

### 1.8 Authoritative Command Flow

Creation follows this sequence:

1. Validate `Idempotency-Key` and the request body, then calculate the request
   fingerprint.
2. Strongly read the receipt. Replay it or reject mismatched reuse when found.
3. Create a detached core game and the API persistence metadata.
4. Set `gameVersion` to 1 and serialize the state and successful HTTP response.
5. In one DynamoDB transaction, conditionally put the game item and receipt
   item. Both keys must be absent or logically expired.
6. Return only after the transaction succeeds. If the transaction outcome is
   ambiguous or loses a condition race, strongly read the receipt. Replay a
   matching receipt, return `idempotencyKeyReused` for a different fingerprint,
   or return a retryable 503 when the result cannot be resolved.

An existing-game command follows this sequence:

1. Validate `Idempotency-Key`, `Expected-Game-Version`, and the body, then
   calculate the request fingerprint.
2. Strongly read the receipt before performing any version check.
3. Strongly load a detached game snapshot. Treat an elapsed TTL as not found.
4. Compare the request version to the loaded version and reject a mismatch.
5. Execute the command once against the detached game. Run synchronous
   state-affecting callbacks before persistence.
6. Set the resulting version to N+1 and serialize both the complete persistence
   snapshot and final HTTP response before writing anything.
7. In one DynamoDB transaction, conditionally update the game from N to N+1 and
   conditionally create the receipt.
8. Return success only after the transaction commits. On cancellation, strongly
   read the receipt first. Replay a matching receipt, return
   `idempotencyKeyReused` for a different fingerprint, or strongly reload the
   game when no receipt exists. That reload determines whether to return
   `gameNotFound` for expiry, `gameVersionConflict` for a concurrent commit, or
   `gamePersistenceUnavailable` when the result cannot be resolved.

Every accepted, unique POST against an existing game increments the version,
including an accepted command that happens to produce no visible board change.
TTL-only maintenance must not increment the game version.

No process-local lock is relied on for deployed correctness. DynamoDB's
conditional transaction is the serialization point across all API instances.

### 1.9 DynamoDB Data Model

The existing development table is the `BattleHexesDevTable` resource defined
in `battle_hexes_api/dev-database.yml` and deployed by the
`battle-hexes-dev-data` CloudFormation stack. It already has string `pk` and
`sk` keys and a numeric `ttl` attribute with DynamoDB TTL enabled, so its key
schema does not need to change. No index, scan, query, stream, or additional
table is required for the initial model. Other environments must provide an
equivalent table configuration; the API receives the table name through its
environment configuration rather than assuming the development table name.

One item holds the current game snapshot:

```json
{
  "pk": "GAME#<game-uuid>",
  "sk": "SNAPSHOT",
  "item_type": "game",
  "game_id": "<game-uuid>",
  "version": 8,
  "state_schema_version": 1,
  "scenario_id": "d_day_crossroads",
  "scenario_version": "1",
  "state": "<canonical UTF-8 JSON document>",
  "updated_at": 1789171200,
  "ttl": 1789257600
}
```

One item holds each successful command receipt:

```json
{
  "pk": "IDEMPOTENCY#<sha256-of-key>",
  "sk": "RECEIPT",
  "item_type": "command_receipt",
  "request_hash": "<sha256-of-canonical-command>",
  "game_id": "<game-uuid>",
  "game_version": 8,
  "status_code": 200,
  "content_type": "application/json",
  "response_body": "<exact response bytes>",
  "response_headers": {
    "Game-Version": "8"
  },
  "created_at": 1789171200,
  "ttl": 1789257600
}
```

`state` and `response_body` may be stored as DynamoDB binary attributes
containing uncompressed JSON bytes. Keeping one explicit JSON document avoids
DynamoDB numeric conversion leaking into the domain codec and avoids unsafe
Python object serialization. Compression can be considered later if measured
sizes justify it.

For creation, `TransactWriteItems` conditionally puts both items. For a command
at version N, `TransactWriteItems` performs:

```text
Update game snapshot:
    SET state = :state,
        version = :next_version,
        updated_at = :now,
        ttl = :expires
    CONDITION version = :expected_version AND ttl > :now

Put command receipt:
    CONDITION attribute_not_exists(pk) OR ttl <= :now
```

The game and receipt must not be written separately. Separate writes could
commit a combat result without a replay receipt, or publish a receipt for a game
transition that did not commit.

All `GetItem` calls for games and receipts set `ConsistentRead=True`. Eventual
reads are not used even for GET routes, because the database response is the
authoritative state shown to players.

### 1.10 Persistence Document

The persistence document is an internal API format, separate from client-facing
Pydantic schemas such as `GameModel` and `SparseBoard`. Those schemas omit
runtime data and are presentation projections, so they must not be reused as
storage snapshots.

Static board, terrain, objective, road, faction, unit-definition, victory, and
defensive-fire configuration is reloaded from `scenarioId`. The saved
`scenarioVersion` verifies which definition the dynamic state expects. The
initial implementation does not embed a copy of the scenario.

At minimum, the persistence document captures:

- game ID, scenario ID/version, player type IDs, and persistence schema version;
- player order and current player identity;
- turn number, current phase, ordered pending combats, terminal state, and the
  already-computed game status;
- player scores;
- ordered active unit IDs and each scenario unit's disposition, coordinates,
  movement points, and complete defensive-fire runtime flags and modifier;
- reinforcement group `entered` state and ordered arrival-attempt history;
- ordered combat and defensive-fire histories in their core record forms, not
  the grouped client presentation; and
- stable identifiers needed to reconnect shared player, faction, unit, board,
  reinforcement, and controller references during hydration.

The codec preserves collection ordering where it can affect game behavior or
history presentation. It restores the persisted game status instead of asking
API schema code to evaluate game rules.

The current core does not expose a complete public hydration API. Under the
no-core-change constraint, the API codec may need narrowly contained assignment
to core runtime attributes after constructing the object graph from the
scenario. This coupling is isolated in the codec and covered by exhaustive
round-trip tests. It must not spread into routes, HTTP schemas, or repository
implementations.

#### Agent State Policy

The primitive Q-learning player is not a persistence requirement. A saved game
records its `q-learning` player type, but does not record its Q-table,
hyperparameters, turn count, pending last actions, learning flags, or any other
private agent state. Hydration recreates the player using the same configured
baseline Q-table and settings used for a new game. The baseline pickle remains
a trusted deployment artifact and is never written to or read from DynamoDB.

Q-learning updates made while handling one request may affect work within that
request, but can be discarded afterward. Learning continuity across requests,
process restarts, and API instances is explicitly not guaranteed. Losing
`_last_actions` before a later combat callback is acceptable because it only
loses this experimental agent's learning update; it does not lose authoritative
board, combat, score, or turn state.

The minimum implementation does not add a process-local agent cache. Such a
best-effort cache may be added later if useful, and it may produce different
learning behavior when requests reach different instances, but game correctness
must never depend on a cache hit. The in-memory and DynamoDB repositories both
apply this same non-persistent agent-state policy.

Future PPO, AlphaZero, or other agents should default to stateless inference
from the authoritative game snapshot with separately deployed immutable model
artifacts. If a future agent requires per-game recurrent state for correct
inference, that state and its compatibility/versioning rules must be designed
explicitly when the agent is introduced. Production game persistence must not
become a general-purpose RL training store.

The process-global random generator state is not persisted as game state. A new
logical action may generate a new random result. Idempotency receipts ensure a
successfully committed logical action is replayed without exposing a second
result.

### 1.11 Expiry and Purging

Game retention is 24 hours after the last successfully committed game mutation.
Creation counts as the first mutation. Each later successful unique command
sets `ttl` to the commit time plus 24 hours. GET requests, rejected commands,
and idempotent replays do not extend a game's life.

Each command receipt expires 24 hours after its original successful commit and
is not extended. The idempotency guarantee is therefore explicitly bounded to
that period.

DynamoDB TTL deletion is asynchronous and is only the physical purge mechanism.
Every repository read and write also enforces logical expiry:

- A game with `ttl <= now` is immediately treated as not found even if its item
  remains in DynamoDB.
- A mutation condition includes `ttl > now`, preventing an expired game from
  being revived.
- A new item may replace a physically present expired key by using an
  `attribute_not_exists(...) OR ttl <= now` condition.

No scheduled scanner or purge worker is required. DynamoDB TTL removes expired
items eventually without adding a table scan path to the application.

### 1.12 Item-Size Strategy and History

Game history remains inside the snapshot initially. This keeps reconstruction
and versioned commits to one game item, but DynamoDB limits every item to 400
KB. Command receipts face the same limit, and some movement responses duplicate
full game and sparse-board data.

The codec and repository enforce a conservative encoded-item budget, initially
350 KiB, before attempting a transaction. A size failure leaves the previous
game version authoritative and returns a clear capacity error. Logs and metrics
report item size and warn before the limit, without logging game contents.

The implementation specifications must add tests with growing combat,
defensive-fire, and reinforcement histories. If realistic games approach the
budget, a later design will move immutable history into separate ordered items
and add pagination. Silent history truncation is not allowed because the
current game log is part of authoritative game state.

### 1.13 In-Memory Repository Semantics

The in-memory implementation is a local adapter for the same repository
contract, not a simplified mock with different correctness behavior. It must:

- use the same `GameStateCodec` on write and read so callers receive detached
  object graphs;
- atomically commit the game and command receipt under a lock;
- implement the same version and idempotency conflicts;
- use an injectable clock and enforce the same logical TTL boundaries;
- enforce the same state and receipt size budgets; and
- guarantee that an exception before commit leaves the stored game unchanged.

This parity makes local behavior representative of a stateless deployed API and
allows most repository contract tests to run without AWS.

### 1.14 Configuration and Infrastructure

The existing environment configuration selects the implementation:

| Configuration | Repository |
| --- | --- |
| `DYNAMODB_ENABLED=false` | `GameRepositoryInMemory` |
| `DYNAMODB_ENABLED=true` with `DDB_TABLE_NAME` | `GameRepositoryDynamoDB` |

Invalid enabled configuration fails startup. A deployed environment must not
silently fall back to memory when DynamoDB is unavailable.

The existing `BattleHexesDevTable` provides on-demand billing, encryption,
point-in-time recovery, `pk`/`sk`, and TTL on `ttl`; its schema does not need to
change. Other environments must provision the same required key and TTL
configuration. DynamoDB authorizes `TransactWriteItems` through the permissions for its
underlying item actions, so this transaction shape requires `PutItem` and
`UpdateItem`, not a `dynamodb:TransactWriteItems` IAM action. Unused scan, query,
batch, index, and stream permissions are not needed for this design and should
not be added as dependencies.

Readiness in DynamoDB mode verifies that the selected repository is DynamoDB,
the table is active, its key schema is the expected string `pk`/`sk` schema,
and TTL is enabled on `ttl`. This may require
`dynamodb:DescribeTimeToLive`. `/health` remains independent of external
dependencies. In-memory mode is ready without AWS access.

### 1.15 Frontend Coordination

Persistence remains an API responsibility and does not introduce database code
outside `battle_hexes_api`. The HTTP contract changes require a coordinated web
deployment, with no backward-compatibility layer.

The frontend must:

- retain `gameVersion` from every successful create, load, and command response;
- send that version as `Expected-Game-Version` for the next existing-game POST;
- generate one `Idempotency-Key` per logical POST, including game creation;
- retain the key, exact body, and expected version across network or retryable
  persistence failures;
- apply the returned version before starting a subsequent CPU or human command;
- serialize commands for one game and disable duplicate UI submission while a
  command is in flight;
- on `gameVersionConflict`, GET and apply authoritative state rather than
  resubmitting stale intent with a new version; and
- parse structured API errors and avoid advancing local turn/phase state after
  a failed command.

Frontend and API changes ship together so every deployed game flow remains
functional. No temporary optional-header behavior is required.

### 1.16 Failure Handling and Observability

A successful response means the game snapshot and command receipt are durable.
If serialization or persistence fails before commit, no new version is visible
and the client can retry with the same key and expected version.

If a DynamoDB call times out with an ambiguous result, the repository strongly
reads the receipt. A matching receipt proves success and is replayed. An absent
receipt after bounded resolution returns 503; the API must not blindly rerun
and claim a second success.

Operational telemetry should include repository implementation, operation,
latency, game version, outcome category, transaction conflicts, replay count,
item sizes, expiry count, and DynamoDB error category. Logs must not contain raw
idempotency keys, complete game snapshots, model artifacts, or response bodies.

### 1.17 Test Strategy

Implementation specifications must cover at least:

- one repository contract suite run against in-memory and DynamoDB adapters;
- detached read/write behavior and rollback after command or serialization
  failure;
- codec round trips for every scenario and player type at creation and after
  movement, combat, reinforcement, scoring, and completion transitions;
- preservation of ordered units, pending combats, logs, defensive-fire state,
  reinforcement state, scores, and terminal status;
- reconstruction of the Q-learning player from its configured baseline without
  serializing Q-table, last-action, or online-learning state;
- scenario-version and state-schema incompatibility;
- two different commands racing from one version, with exactly one commit and
  one version conflict;
- concurrent identical idempotency keys, with one committed game transition
  and identical replayed responses;
- create idempotency, including an ambiguous transaction result;
- same key with a changed route, body, game ID, or expected version;
- retry of random combat after commit without a second authoritative result;
- exact TTL boundary behavior, sliding expiry after successful mutation,
  physically present expired records, and no extension on GET or replay;
- snapshot and receipt size limits before any write occurs;
- HTTP header validation, response versions, structured errors, and CORS
  exposure;
- frontend command serialization, retry key reuse, version updates, and stale
  state recovery; and
- CloudFormation linting plus readiness behavior for wrong table schema,
  disabled TTL, missing permissions, and unavailable DynamoDB.

Botocore stubs are appropriate for request construction and error translation,
but transaction and conditional-write behavior also needs integration coverage
against DynamoDB Local, another compatible test service, or a disposable AWS
test table. Mocks alone do not establish DynamoDB concurrency semantics.

### 1.18 Implementation Decomposition

This design can produce several focused implementation specifications:

1. API persistence document, codec, repository interface, in-memory adapter,
   and shared contract tests.
2. DynamoDB repository, atomic conditional transactions, expiry behavior,
   configuration, readiness, IAM, and infrastructure tests.
3. API command service, version and idempotency HTTP contracts, route migration,
   response receipts, and concurrency tests.
4. Frontend version tracking, idempotency keys, retry/conflict handling, and
   coordinated end-to-end behavior.

These are implementation boundaries, not independent production rollout
phases. Persistence, optimistic concurrency, idempotency, and the updated
frontend contract must all be present when the feature is enabled in the
deployed environment.

## Open Questions

No questions.
