---
title: Persistence Contracts and Command Identity
version: 1.0
date_created: 2026-09-19
last_updated: 2026-09-19
tags: [architecture, game-persistence, api, idempotency]
---

# Introduction

This specification defines the API-owned repository boundary and deterministic
command identity required before persistence is connected to HTTP routes. It is
increment 3.1 of the game-persistence implementation schedule.

## 1. Purpose & Scope

This increment adds storage-neutral types, repository outcomes, idempotency-key
validation and hashing, request fingerprinting, an injectable clock, and a
shared encoded-item budget. All code belongs in `battle_hexes_api`; no core,
route, schema, or frontend behavior changes are in scope.

The contracts must support both in-memory and DynamoDB adapters without exposing
provider-specific types. Implementing either adapter, the state codec, command
service, or new HTTP header enforcement is deferred.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Command | One validated state-affecting HTTP POST request. |
| Command identity | The digested idempotency key and fingerprint used to identify and compare commands. |
| Fingerprint | SHA-256 digest of a canonical representation of the command method, route, expected version, and validated body. |
| Receipt | Immutable record of a successfully committed command and its exact replayable response. |
| Logical expiry | A record is expired when `expires_at <= clock.now()`, regardless of physical deletion. |
| Encoded-item budget | Maximum permitted size of one complete persistence item: 350 KiB (358,400 bytes). |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Define `GameRepository` as an API-owned protocol or abstract
  interface with the operations in section 4. Implementations must be
  substitutable and must not appear in consumers' type signatures.
- **REQ-002**: Define immutable storage-neutral value types for `StoredGame`,
  `CommandIdentity`, and `CommandReceipt`. Validate their invariants at
  construction.
- **REQ-003**: Represent game versions as positive integers. Creation stores
  version 1; mutation contracts accept an expected version and a stored game
  whose version is exactly expected version plus one.
- **REQ-004**: Represent `created_at`, `updated_at`, and `expires_at` as integral
  Unix epoch seconds in UTC. A clock returns integral Unix epoch seconds.
- **REQ-005**: Accept an idempotency key only when it is 1 through 255 ASCII
  characters, contains no control or whitespace characters, and is unchanged
  by validation. Reject surrounding whitespace rather than trimming it.
- **REQ-006**: Hash the UTF-8 bytes of a validated idempotency key with SHA-256
  and expose only the 64-character lowercase hexadecimal digest to persistence
  and logging code. The raw key must not be retained in persistence types.
- **REQ-007**: Compute a request fingerprint from the canonical document in
  section 4. The output is a 64-character lowercase SHA-256 hexadecimal digest.
- **REQ-008**: Fingerprinting accepts only a validated JSON-compatible body.
  Object keys must be strings; non-finite numbers and non-JSON values are
  rejected. An absent body is represented as JSON `null`.
- **REQ-009**: Normalize the HTTP method to uppercase. Normalize a route by
  requiring an absolute path, removing a trailing slash except for `/`, and
  excluding scheme, authority, query, and fragment. Percent-encoded octets are
  uppercased but not decoded. No other path rewriting is allowed.
- **REQ-010**: Canonical JSON must use UTF-8, lexicographically sorted object
  keys, no insignificant whitespace, JSON literals for booleans and null, and
  unescaped Unicode except characters JSON requires to be escaped. The
  implementation must produce the same bytes independent of dictionary order,
  locale, and process.
- **REQ-011**: Repository failures must use only the outcomes/errors in section
  4. Provider exceptions and transaction cancellation details must not cross
  the repository boundary.
- **REQ-012**: A receipt stores exact response body bytes, status code, content
  type, application-controlled response headers, resulting game ID and version,
  request fingerprint, creation time, and expiry time. Header names and values
  are stored without provider-generated transport headers.
- **REQ-013**: The clock and item-size measurement are injected dependencies.
  Production code may use a system clock; tests must be able to set time and
  encoded size deterministically.
- **REQ-014**: A shared budget policy accepts an encoded byte count at or below
  358,400 and returns a storage-neutral capacity error above it. Repositories
  must apply it to the complete encoded game item and complete encoded receipt,
  not only `state` or `response_body`.
- **CON-001**: Persistence contracts must not import AWS SDK types, FastAPI
  request/response types, or client-facing Pydantic schemas.
- **CON-002**: This increment must not modify `battle_hexes_core`, activate a
  repository, require headers on routes, or change observable API behavior.
- **GUD-001**: Use frozen dataclasses and `typing.Protocol` unless an equivalent
  dependency-free Python construct provides clearer immutable contracts.

## 4. Interfaces & Data Contracts

The names below are normative; exact module layout may follow existing API
package conventions.

### 4.1 Value types

```python
@dataclass(frozen=True)
class CommandIdentity:
    key_digest: str
    request_fingerprint: str

@dataclass(frozen=True)
class StoredGame:
    game_id: str
    version: int
    state_schema_version: int
    scenario_id: str
    scenario_version: str
    state: bytes
    updated_at: int
    expires_at: int

@dataclass(frozen=True)
class CommandReceipt:
    identity: CommandIdentity
    game_id: str
    game_version: int
    status_code: int
    content_type: str
    response_body: bytes
    response_headers: Mapping[str, str]
    created_at: int
    expires_at: int
```

`state` is the API codec's canonical UTF-8 persistence document. Mapping values
must be defensively copied into an immutable representation so callers cannot
mutate a receipt after construction.

### 4.2 Repository interface

```python
class GameRepository(Protocol):
    def load_game(self, game_id: str) -> StoredGame: ...
    def find_receipt(self, key_digest: str) -> CommandReceipt | None: ...
    def create_game(
        self, game: StoredGame, receipt: CommandReceipt
    ) -> None: ...
    def commit_command(
        self,
        expected_version: int,
        game: StoredGame,
        receipt: CommandReceipt,
    ) -> None: ...
```

`load_game` and `find_receipt` are authoritative reads. `create_game` and
`commit_command` atomically persist both supplied records or neither. A missing
receipt is returned as `None`; all other non-success outcomes use these
storage-neutral errors:

| Error | Meaning |
| --- | --- |
| `GameNotFoundError` | The game is absent or logically expired. |
| `GameAlreadyExistsError` | Creation found an unexpired game with the same ID. |
| `GameVersionConflictError` | The current version differs from `expected_version`. Carries expected and current version when known. |
| `IdempotencyConflictError` | An unexpired receipt key already identifies a different fingerprint. |
| `SavedGameIncompatibleError` | State or scenario version cannot be loaded. Reserved for codec-backed repository reads. |
| `PersistenceCapacityError` | A complete game item or receipt exceeds the encoded-item budget. Carries item kind, measured bytes, and limit. |
| `PersistenceUnavailableError` | Storage is unavailable or a commit outcome cannot be resolved. |

The later repository implementations may return an existing matching receipt
when resolving a commit race, but they must never report provider-specific
conditions. Exact race-resolution behavior is specified by increments 3.3,
3.4, and 3.8.

### 4.3 Fingerprint document

The fingerprint input is the SHA-256 digest of these canonical JSON bytes:

```json
{"body":{"destination":{"column":4,"row":2}},"expectedGameVersion":7,"method":"POST","route":"/games/6e6f/movements"}
```

The document always contains all four fields. `expectedGameVersion` is `null`
for creation. The validated body uses API JSON names (camelCase), not internal
Python attribute names. The normalized route includes the concrete game ID.

### 4.4 Utilities

```python
class Clock(Protocol):
    def now(self) -> int: ...

class EncodedItemSizer(Protocol):
    def size_bytes(self, item: Mapping[str, object]) -> int: ...

class EncodedItemBudget:
    limit_bytes: int = 350 * 1024
    def require_fits(self, item_kind: str, encoded_size_bytes: int) -> None: ...
```

Each adapter must provide an `EncodedItemSizer` that measures its complete
storage representation. Contract tests inject a deterministic sizer so boundary
semantics are identical without coupling contracts to DynamoDB.

## 5. Acceptance Criteria

- **AC-001**: Given the same validated command values in any mapping insertion
  order, fingerprinting returns the same digest across repeated processes.
- **AC-002**: Changing the method, normalized route (including game ID), expected
  version, or any body value changes the fingerprint.
- **AC-003**: Semantically identical routes with only a trailing slash or
  percent-hex casing difference produce the same fingerprint; query strings are
  rejected rather than silently included.
- **AC-004**: Boundary keys of 1 and 255 valid ASCII characters are accepted;
  empty, 256-character, whitespace-containing, control-containing, and
  non-ASCII keys are rejected.
- **AC-005**: No object returned by key validation or identity construction
  contains or renders the raw idempotency key.
- **AC-006**: A fixed clock makes stored timestamps and exact expiry checks
  deterministic; at `expires_at == now`, the record is expired.
- **AC-007**: Encoded items of 358,400 bytes are accepted and items of 358,401
  bytes raise `PersistenceCapacityError` with deterministic metadata.
- **AC-008**: Contract modules import without FastAPI, boto3/botocore, or
  `battle_hexes_core` and expose no types from those packages.
- **AC-009**: Existing route tests pass unchanged, demonstrating that this
  increment does not activate the new HTTP contract.

## 6. Test Automation Strategy

- Add focused unit tests for key validation/digests, canonical JSON,
  fingerprint field sensitivity, route normalization, immutable value-type
  invariants, the fixed clock, and both item-budget boundaries.
- Use published SHA-256 vectors and hard-coded expected fingerprint digests so
  tests do not reproduce the implementation algorithm.
- Add interface-level tests with a minimal fake repository to verify consumer
  typing and storage-neutral errors. Full shared adapter contract tests are
  deferred to increment 3.3.
- Run `./server-side-checks.sh`; no new coverage threshold is introduced.

## 7. Rationale & Context

Digesting keys prevents credentials-like client tokens from entering durable
storage or telemetry. Fingerprinting validated semantic JSON avoids differences
from insignificant wire formatting while detecting reuse for another command.
Immutable, provider-neutral values keep command orchestration independent of
DynamoDB and make the in-memory adapter exercise the same observable contract.

## 8. Dependencies & External Integrations

- **DEP-001**: Python standard-library JSON, hashing, time, dataclass, and typing
  facilities are sufficient; no new runtime dependency is required.
- **DEP-002**: [`docs/design.md`](../../docs/design.md), sections 1.4-1.9 and
  1.11-1.13, is authoritative if this specification omits a persistence rule.
- **DEP-003**: The state bytes and compatibility checks consumed by
  `StoredGame` are supplied by increment 3.2.
- No external system is contacted or configured in this increment.

## 9. Examples & Edge Cases

| Input variation | Required result |
| --- | --- |
| Body object keys inserted in a different order | Same fingerprint |
| `/games/abc/movements/` vs `/games/abc/movements` | Same fingerprint |
| `/games/abc` vs `/games/ABC` | Different fingerprint |
| Expected version `7` vs `8` | Different fingerprint |
| Expected version absent vs JSON body containing `null` | Distinct fields; absence is represented only by `expectedGameVersion: null` |
| Key ` action-1 ` | Invalid; do not trim |
| `expires_at == clock.now()` | Expired |
| Exact 350 KiB complete item | Accepted |

## 10. Validation Criteria

Implementation is compliant when every acceptance criterion has an automated
test, the API test and lint suite passes, public contracts contain no
provider/framework types, and a code search confirms that live routes do not
import or enforce the new command-identity utilities.

## 11. Related Specifications / Further Reading

- [Game Persistence Implementation Specification Schedule](implementation-schedule.md)
- [Battle Hexes Application Design](../../docs/design.md)

## 12. Open Questions

No questions.
