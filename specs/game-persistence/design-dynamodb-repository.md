---
title: DynamoDB Repository
version: 1.0
date_created: 2026-09-26
last_updated: 2026-09-26
tags: [design, game-persistence, api, dynamodb, repository]
---

# Introduction

This specification defines increment 3.8 of the game-persistence schedule: a
DynamoDB adapter with the same observable contract as the in-memory repository.

## 1. Purpose & Scope

Implement `GameRepositoryDynamoDB` in `battle_hexes_api`. It must use strongly
consistent reads and conditional transactions to persist each game snapshot and
successful command receipt atomically.

This increment includes item mapping, size enforcement, provider-error
translation, transaction reconciliation, and DynamoDB integration tests. It does
not select the adapter at runtime, change routes or HTTP behavior, modify
infrastructure or readiness checks, add telemetry, or modify `battle_hexes_core`.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Ambiguous outcome | A transaction call failed without proving whether DynamoDB committed it. |
| Logical expiry | An item is unavailable when `ttl <= clock.now()`, regardless of physical presence. |
| Reconciliation | Strongly consistent reads used to classify a cancelled, competing, or ambiguous transaction. |
| Transaction race | Multiple writers compete for a game version, game ID, or receipt key. |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Add `GameRepositoryDynamoDB` under
  `battle_hexes_api.persistence`. Inject the table name, a low-level DynamoDB
  client, `Clock`, `EncodedItemSizer`, and `EncodedItemBudget`; do not construct
  AWS clients inside repository methods.
- **REQ-002**: Implement only the existing `GameRepository` methods and return
  only `StoredGame`, `CommandReceipt`, or storage-neutral errors. No AWS type,
  response, exception, or cancellation reason may cross the adapter boundary.
- **REQ-003**: Encode game and receipt items exactly as specified in section 4.
  Isolate mapping and validation from transaction orchestration. Malformed or
  missing required attributes must become `PersistenceUnavailableError` without
  exposing item contents.
- **REQ-004**: `load_game` and `find_receipt` must use `GetItem` with
  `ConsistentRead=True`. An absent or logically expired game raises
  `GameNotFoundError`; an absent or expired receipt returns `None`. Reads never
  refresh TTL.
- **REQ-005**: Before any write, validate the game/receipt pairing and measure
  each complete encoded item independently. A measured size above 358,400 bytes
  raises `PersistenceCapacityError` and sends no transaction request.
- **REQ-006**: `create_game` accepts version 1 only and uses one
  `TransactWriteItems` request containing two conditional puts. Both the game
  key and receipt key may be written only when absent or logically expired.
- **REQ-007**: `commit_command` accepts candidate version
  `expected_version + 1` and uses one transaction containing: (1) an update of
  the game item conditioned on `version = expected_version AND ttl > now`; and
  (2) a receipt put conditioned on absence or `ttl <= now`. The update must set
  every mutable game attribute so the stored item equals the candidate.
- **REQ-008**: Use one `clock.now()` value for all logical-expiry conditions in
  a transaction attempt. Persist caller-supplied timestamps and TTL values
  unchanged; the repository must not calculate or extend retention.
- **REQ-009**: Raw idempotency keys must never enter keys, items, expressions,
  logs, or exceptions. Use `GAME#<game_id>`/`SNAPSHOT` and
  `IDEMPOTENCY#<key_digest>`/`RECEIPT` keys.
- **REQ-010**: On a transaction cancellation or ambiguous write result,
  reconcile before returning: strongly read the receipt first; return a
  matching receipt, raise `IdempotencyConflictError` for a different
  fingerprint, or continue according to section 4.3 when absent.
- **REQ-011**: A matching receipt found before or after a write returns as the
  authoritative result without another write. This applies even when the game
  is absent, expired, or at a later version.
- **REQ-012**: When reconciliation finds no receipt, creation returns
  `GameAlreadyExistsError` only for a proven conditional race with a live game;
  an ambiguous creation returns `PersistenceUnavailableError`. Mutation must
  strongly reload the game and return `GameNotFoundError` for absence/expiry,
  `GameVersionConflictError` for another version, or
  `PersistenceUnavailableError` when the expected version remains current.
- **REQ-013**: Translate throttling, authentication, endpoint, serialization,
  internal-service, and exhausted SDK retry failures to
  `PersistenceUnavailableError`. Preserve known current versions only in
  `GameVersionConflictError`; do not expose provider messages or request IDs.
- **REQ-014**: Reconciliation must be bounded: one receipt read and, only when
  required, one game read per failed transaction call. If either read fails,
  return `PersistenceUnavailableError` and never retry game behavior.
- **REQ-015**: A failed or unresolved operation must never be reported as
  success from the locally supplied candidate. Success requires a completed
  transaction or a strongly read matching receipt.
- **CON-001**: Do not use `Scan`, `Query`, batch operations, indexes, streams,
  PartiQL, or separate/non-transactional game and receipt writes.
- **CON-002**: Do not add a process-local correctness lock, shadow-write path,
  fallback to memory, table creation, readiness validation, or runtime
  repository selection.
- **GUD-001**: Keep item codecs, transaction request construction, and outcome
  reconciliation as cohesive collaborators rather than one large adapter
  module.

## 4. Interfaces & Data Contracts

### 4.1 Construction

```python
class GameRepositoryDynamoDB:
    def __init__(
        self,
        table_name: str,
        client: object,
        clock: Clock,
        item_sizer: EncodedItemSizer,
        item_budget: EncodedItemBudget,
    ) -> None: ...
```

The class implements the existing `GameRepository`; it introduces no
provider-specific consumer interface.

### 4.2 Item mappings

| Value | DynamoDB attributes |
| --- | --- |
| `StoredGame` | `pk`, `sk`, `item_type="game"`, `game_id`, `version`, `state_schema_version`, `scenario_id`, `scenario_version`, binary `state`, `updated_at`, `ttl=expires_at` |
| `CommandReceipt` | `pk`, `sk`, `item_type="command_receipt"`, `request_hash`, `game_id`, `game_version`, `status_code`, `content_type`, binary `response_body`, `response_headers`, `created_at`, `ttl=expires_at` |

Numbers must be represented without float conversion. Reads must validate the
expected key, item type, field types, positive versions, digests, timestamps,
and value-object invariants before returning a detached value.

### 4.3 Reconciliation decision order

1. Strongly read the candidate receipt key.
2. If live and matching, return it; if live and nonmatching, raise
   `IdempotencyConflictError`; treat an expired receipt as absent.
3. For a known create condition failure, strongly read the game and report
   `GameAlreadyExistsError` only when it is live; otherwise report unavailable.
4. For a mutation, strongly read the game. Report not found for absence or
   expiry, version conflict for a different live version, and unavailable when
   the expected live version remains.
5. For an ambiguous creation with no receipt, report unavailable without using
   game presence as proof that this transaction committed.

Cancellation-reason positions must correspond to a stable transaction item
order. Unknown, missing, or contradictory reasons are ambiguous, not success.

## 5. Acceptance Criteria

- **AC-001**: Every game and receipt read requests strong consistency and
  enforces expiry at the exact `ttl == now` boundary.
- **AC-002**: A successful create or mutation makes its snapshot and receipt
  visible together and returns the authoritative receipt.
- **AC-003**: Two different commands racing from version N produce one version
  N+1; the loser receives a version conflict and leaves no orphan receipt.
- **AC-004**: Concurrent identical commands produce one transition and both
  callers receive byte-identical receipt content.
- **AC-005**: A matching receipt takes precedence over game absence, expiry,
  or version state; a nonmatching receipt takes precedence as an idempotency
  conflict.
- **AC-006**: Physically present expired game and receipt items are readable as
  absent and replaceable by a valid creation/commit.
- **AC-007**: Items at 358,400 bytes may be submitted; either item at 358,401
  bytes fails before the DynamoDB client receives a write.
- **AC-008**: A timeout followed by a matching receipt returns success; an
  unresolved timeout returns `PersistenceUnavailableError` and never returns
  the candidate receipt.
- **AC-009**: Stubbed requests contain exactly one transaction with the required
  expressions, values, table name, keys, and two write operations; no forbidden
  DynamoDB operation is invoked.
- **AC-010**: Runtime repository selection and all route behavior remain
  unchanged.

## 6. Test Automation Strategy

- Run the adapter-neutral repository contract suite against a disposable table
  in DynamoDB Local, another compatible service, or a disposable AWS account.
- Add botocore-stubbed unit tests for item encoding/decoding, strong-read flags,
  exact transaction requests, size rejection, and provider-error translation.
- Add integration races for different commands and identical identities, plus
  tests for ambiguous create/mutation results and physically retained expired
  items. Tests must use bounded synchronization and clean up their own keys.
- Assert public outcomes and final strongly read state; do not assert private
  helper calls. Run `./server-side-checks.sh`; no new coverage threshold is
  required.

## 7. Rationale & Context

The transaction is the cross-process serialization point. Receipt-first
reconciliation preserves replay after a lost response, while logical TTL checks
avoid depending on DynamoDB's asynchronous physical deletion. Provider-neutral
outcomes keep the command service substitutable across repository adapters.

## 8. Dependencies & External Integrations

- **DEP-001**: Increments 3.1 and 3.3 define persistence values, errors, commit
  return values, size policy, and the shared repository contract suite.
- **DEP-002**: Increment 3.2 supplies canonical state bytes; the repository does
  not invoke game rules or hydrate core objects.
- **DEP-003**: The existing boto3/botocore runtime dependency supplies the
  DynamoDB client and stubbing support.
- **DEP-004**: A test table must have string partition/sort keys named `pk` and
  `sk`. TTL configuration and production IAM/readiness belong to increment 3.9.
- **DEP-005**: [`docs/design.md`](../../docs/design.md), sections 1.4, 1.7-1.9,
  1.11-1.12, and 1.16-1.17, remains authoritative where this spec is silent.

## 9. Examples & Edge Cases

| Situation | Required result |
| --- | --- |
| Matching receipt, expired game | Return receipt without a game read. |
| Different fingerprint, current game version | Raise idempotency conflict. |
| Mutation cancellation, no receipt, version N+1 | Raise version conflict with N+1. |
| Mutation cancellation, no receipt, version N | Raise persistence unavailable. |
| Ambiguous creation, no receipt, game present | Raise persistence unavailable. |
| Expired physical receipt key | Transaction may replace it without a delete. |

## 10. Validation Criteria

The increment is complete when the shared contract suite passes for both
adapters, DynamoDB request/error unit tests pass, integration concurrency and
expiry tests pass against a compatible service, server checks pass, and code
search finds no runtime construction or route import of
`GameRepositoryDynamoDB`.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.8.
- [Persistence contracts and command identity](architecture-persistence-contracts-command-identity.md).
- [Contract-compliant in-memory repository](design-contract-compliant-in-memory-repository.md).
- [Command service foundation](design-command-service-foundation.md).
- [Application persistence design](../../docs/design.md).

## 12. Open Questions

No questions.
