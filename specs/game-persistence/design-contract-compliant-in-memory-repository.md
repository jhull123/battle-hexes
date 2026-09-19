---
title: Contract-Compliant In-Memory Repository
version: 1.0
date_created: 2026-09-19
last_updated: 2026-09-19
tags: [design, game-persistence, api, repository, testing]
---

# Introduction

This specification defines increment 3.3 of the game-persistence schedule: an
in-memory repository whose observable behavior is reusable as the contract for
the future DynamoDB adapter.

## 1. Purpose & Scope

Implement `GameRepositoryInMemory` and a storage-adapter contract suite inside
`battle_hexes_api`. The adapter stores only persistence values, returns
detached snapshots, atomically publishes a game and its successful command
receipt, and enforces version, expiry, idempotency, and capacity rules.

This increment does not select the repository at runtime, change routes or HTTP
behavior, implement command orchestration, or modify `battle_hexes_core`.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Commit | Atomic publication of one game snapshot and one completed receipt. |
| Detached | A value or hydrated game whose mutation cannot alter repository state or another load result. |
| Logical expiry | A record is unavailable when `expires_at <= clock.now()`, even if still physically stored. |
| Matching receipt | An unexpired receipt with the same key digest and request fingerprint as the candidate. |
| Contract suite | Adapter-neutral tests executed through the `GameRepository` interface. |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Add `GameRepositoryInMemory` under
  `battle_hexes_api.persistence`. It must implement the increment 3.1
  `GameRepository` interface and expose no additional operations to consumers.
- **REQ-002**: Inject `Clock`, `EncodedItemSizer`, and `EncodedItemBudget`.
  Tests must control time and measured item sizes without sleeping or creating
  oversized payloads.
- **REQ-003**: Keep games keyed by `game_id` and receipts keyed service-wide by
  `CommandIdentity.key_digest`. Never retain a raw idempotency key or a decoded
  core `Game` in repository storage.
- **REQ-004**: Defensively copy all accepted and returned values, including
  bytes and header mappings. Each `load_game` result must be independently
  decodable by `GameStateCodec`; decoding two loads must produce distinct core
  object graphs. The repository must not cache codec output.
- **REQ-005**: `load_game` must raise `GameNotFoundError` when no game exists or
  `expires_at <= now`. `find_receipt` must return `None` under the equivalent
  conditions. Neither operation changes expiry.
- **REQ-006**: `create_game` accepts only game version 1. Under one lock it must
  require the game ID to be absent or expired and the receipt key to be absent
  or expired, then publish both records together.
- **REQ-007**: `commit_command` must require an unexpired stored game whose
  version equals `expected_version`, and a candidate game with the same ID and
  version `expected_version + 1`. Under the same lock it must replace the game
  and create the receipt together.
- **REQ-008**: A successful unique create or mutation must store the supplied
  timestamps exactly. The repository must not calculate or refresh expiry.
  Expired physical entries may be removed lazily but must be replaceable.
- **REQ-009**: Before publishing either record, measure the adapter's complete
  encoded game item and complete encoded receipt. Apply the 358,400-byte budget
  independently. A capacity failure for either item publishes neither.
- **REQ-010**: Validate that a receipt's game ID and game version equal the
  candidate game's ID and version. Invalid input must fail before publication.
- **REQ-011**: For an unexpired receipt with the candidate key digest, a
  different fingerprint raises `IdempotencyConflictError` without changing
  either record. A matching fingerprint returns the already stored receipt and
  performs no write, version change, or expiry extension.
- **REQ-012**: Both atomic methods return the authoritative `CommandReceipt`:
  the supplied detached receipt after a new commit, or the existing detached
  receipt for a matching-key race. Update the increment 3.1 protocol return
  annotations from `None` to `CommandReceipt`; no other contract shape changes.
- **REQ-013**: For a unique receipt key, creation against an unexpired game ID
  raises `GameAlreadyExistsError`. Mutation against an absent or expired game
  raises `GameNotFoundError`; a version mismatch raises
  `GameVersionConflictError` with expected and current versions.
- **REQ-014**: Candidate validation, sizing, copying, and all fallible
  preparation must finish before publication. An exception from command code,
  codec encoding/decoding, sizing, validation, or commit must leave the prior
  authoritative game and receipt set unchanged.
- **REQ-015**: All reads and commits must synchronize access to both maps with
  one repository-owned lock. Check time and all commit preconditions while
  holding that lock. The lock must not be module-global.
- **REQ-016**: Create one adapter-neutral contract suite. Its tests receive a
  repository factory plus controllable clock and sizer; they must not inspect
  internal maps, lock types, private helpers, or provider calls.
- **CON-001**: Production persistence modules must not import test utilities,
  FastAPI request/response types, boto3/botocore, or client-facing schemas.
- **CON-002**: Do not activate this adapter, replace existing route storage, or
  enforce the new HTTP command headers in this increment.
- **GUD-001**: Use a standard mutual-exclusion lock. Correctness must not depend
  on the Python Global Interpreter Lock or mutable object identity.

## 4. Interfaces & Data Contracts

### 4.1 Repository construction and refined commit results

```python
class GameRepositoryInMemory:
    def __init__(
        self,
        clock: Clock,
        item_sizer: EncodedItemSizer,
        item_budget: EncodedItemBudget,
    ) -> None: ...

class GameRepository(Protocol):
    def load_game(self, game_id: str) -> StoredGame: ...
    def find_receipt(self, key_digest: str) -> CommandReceipt | None: ...
    def create_game(
        self, game: StoredGame, receipt: CommandReceipt
    ) -> CommandReceipt: ...
    def commit_command(
        self,
        expected_version: int,
        game: StoredGame,
        receipt: CommandReceipt,
    ) -> CommandReceipt: ...
```

Returning the authoritative receipt lets the later command service distinguish
a new commit from a simultaneous matching request by comparing/replaying the
returned response. It also gives DynamoDB the same race-resolution contract.

### 4.2 Commit decision order

Within the lock, both atomic methods must apply this order:

1. Read `now` once.
2. If an unexpired receipt occupies the key, reject a different fingerprint or
   return a detached copy of the matching receipt.
3. Treat expired records as absent and evaluate game existence/version
   preconditions.
4. Publish the fully prepared game and receipt as one critical-section update.
5. Return a detached copy of the stored receipt.

Structural validation occurs before the locked sequence. For a unique or
expired receipt key, capacity measurement occurs after step 2 and before game
preconditions or publication. A matching receipt therefore takes precedence
over capacity, game absence, expiry, and stale versions, preserving retry
semantics without measuring or writing the losing candidate.

### 4.3 Encoded-size representation

The in-memory adapter must define deterministic mapping encoders containing the
same logical fields as the DynamoDB game and receipt items in
[`docs/design.md`](../../docs/design.md), section 1.9. The injected sizer
measures those complete mappings, including keys, metadata, state/body bytes,
and response headers. The mappings are size-calculation inputs only; stored
values remain `StoredGame` and `CommandReceipt` copies.

## 5. Acceptance Criteria

- **AC-001**: Given one stored snapshot, two loads and codec decodes yield
  equal observable games with no shared mutable graph; mutating either result
  does not change a later load.
- **AC-002**: Given a valid create or mutation, its game and receipt become
  visible together and the returned receipt equals the stored receipt.
- **AC-003**: Given any pre-publication exception, neither a new version nor a
  candidate receipt is observable afterward.
- **AC-004**: Given two different commands racing from version N, exactly one
  stores version N+1; the other receives a version conflict, and no orphan
  receipt exists.
- **AC-005**: Given simultaneous commits with the same key and fingerprint,
  exactly one transition is stored and both calls return detached copies of
  the same authoritative receipt.
- **AC-006**: Reusing an unexpired key with a different fingerprint raises an
  idempotency conflict even when its game is expired, missing, or newer.
- **AC-007**: At `expires_at == now`, reads treat a record as expired, mutation
  cannot revive it, and creation may replace its physical key.
- **AC-008**: Load, receipt lookup, rejected commits, and matching receipt
  replay preserve all timestamps. A successful mutation stores only the
  caller-supplied later expiry.
- **AC-009**: A complete item measured at 358,400 bytes commits; either game or
  receipt measured at 358,401 bytes raises `PersistenceCapacityError` and
  leaves both stores unchanged.
- **AC-010**: Existing route tests pass unchanged and code search confirms no
  route imports or instantiates `GameRepositoryInMemory`.

## 6. Test Automation Strategy

- Put shared tests in a repository-contract module that can later be
  parameterized with in-memory and DynamoDB factories.
- Cover create/load, mutation, detached codec hydration, matching replay,
  changed-fingerprint reuse, missing/expired records, stale versions, exact
  TTL and capacity boundaries, invalid receipt/game pairing, and rollback.
- Use `threading.Barrier` plus bounded joins for two-writer race tests. Assert
  public outcomes and final reads, not execution order.
- Simulate command and codec failures before invoking the repository; inject a
  raising sizer for repository-side preparation failure.
- Run `./server-side-checks.sh`. No new coverage percentage is required.

## 7. Rationale & Context

Detached codec hydration prevents local development from accidentally relying
on process-shared core objects. One lock is the in-memory serialization point
corresponding to DynamoDB's conditional transaction. Checking receipts first
ensures a retry can replay after the original game has advanced or expired.

## 8. Dependencies & External Integrations

- **DEP-001**: Increment 3.1 supplies repository value types, errors, clock,
  identity, sizer, and budget contracts.
- **DEP-002**: Increment 3.2 supplies `GameStateCodec` for detached-object
  assertions and command-side serialization/hydration.
- **DEP-003**: [`docs/design.md`](../../docs/design.md), sections 1.4-1.13 and
  1.16-1.17, remains authoritative where this specification is silent.
- No external service or new runtime dependency is required.

## 9. Examples & Edge Cases

| Situation | Required result |
| --- | --- |
| Expired receipt, live expected game version | Receipt key is reusable; commit may proceed. |
| Matching receipt, expired game | Return receipt; do not report game not found. |
| Different fingerprint, stale game version | Report idempotency conflict first. |
| Unique key, candidate receipt too large | Capacity error; old game remains authoritative. |
| Create over a physically retained expired game ID | Store version 1 and its receipt atomically. |
| Caller mutates original headers after commit | Stored and subsequently returned headers are unchanged. |

## 10. Validation Criteria

Implementation is compliant when the in-memory adapter passes every shared
contract test repeatedly, race tests terminate without deadlock, the API tests
and lint pass, and no runtime route behavior changes. The contract suite must
be runnable unchanged against increment 3.8 except for adapter fixtures.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.3.
- [Persistence contracts and command identity](architecture-persistence-contracts-command-identity.md), increment 3.1.
- [Game-state codec](design-game-state-codec.md), increment 3.2.
- [Application persistence design](../../docs/design.md), sections 1.4-1.17.

## 12. Open Questions

No questions.
