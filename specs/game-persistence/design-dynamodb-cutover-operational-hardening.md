---
title: DynamoDB Cutover and Operational Hardening
version: 1.0
date_created: 2026-09-28
last_updated: 2026-09-28
tags: [design, game-persistence, api, dynamodb, operations]
---

# Introduction

This specification defines increment 3.10 of the game-persistence schedule: the
controlled activation of DynamoDB as the authoritative deployed repository and
the operational evidence required to keep or reverse that activation safely.

## 1. Purpose & Scope

Activate the increment 3.8 DynamoDB adapter through the validated increment 3.9
configuration, instrument persistence behavior, and verify the production
failure model across processes, restarts, races, retries, expiry, and large
histories.

In scope are API composition, storage-neutral telemetry, integration and
deployment verification, and a coordinated configuration rollback procedure.
Out of scope are repository semantics, table/schema changes, data migration,
dual writes, caching, game-rule changes, frontend protocol changes, and new
public endpoints. Existing games are not copied between memory and DynamoDB.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Authoritative repository | The only repository used for game reads and writes by a running API process. |
| Cutover | Deployment configuration change from explicit in-memory mode to DynamoDB mode. |
| Ambiguous result | A write response that does not prove whether its transaction committed. |
| Rollback | Coordinated restoration of the prior backend version/configuration; it does not migrate DynamoDB games into memory. |
| Safe item budget | The existing 358,400-byte limit independently applied to each encoded DynamoDB item. |

## 3. Requirements, Constraints & Guidelines

### 3.1 Runtime activation

- **REQ-001**: During FastAPI lifespan initialization, use the single validated
  persistence configuration to construct exactly one repository: DynamoDB when
  `DYNAMODB_ENABLED=true`, otherwise in-memory. Store it on application state
  and inject it into the command service; routes must not select repositories.
- **REQ-002**: Enabled mode must use `GameRepositoryDynamoDB` with the validated
  table name and the same application DynamoDB client used by startup/readiness
  composition where client lifetime permits. Construction, startup validation,
  or subsequent AWS failure must never select, write to, or read from memory.
- **REQ-003**: Preserve the existing command boundary: return a successful POST
  only after the atomic snapshot-and-receipt transaction completes or a strong
  receipt read proves the ambiguous transaction committed.
- **REQ-004**: In-memory mode remains an explicit local/test option and must
  create no AWS client. `/health`, `/ready`, and startup behavior retain the
  increment 3.9 contracts.

### 3.2 Telemetry and privacy

- **OBS-001**: Emit one completion telemetry event for each repository
  operation (`load_game`, `find_receipt`, `create_game`, `commit_command`) with:
  repository implementation, operation, latency, outcome category, and—when
  known—game version and encoded game/receipt item sizes.
- **OBS-002**: Use bounded outcome categories at minimum for success, replay,
  version conflict, idempotency conflict, not found/expired, capacity exceeded,
  and persistence unavailable. DynamoDB failures must additionally use bounded
  categories for throttling, access/configuration, endpoint/network, service,
  malformed data, and unresolved/unknown failures.
- **OBS-003**: Provide counters or equivalently queryable structured events for
  conflicts, replays, logical expiry, capacity rejection, and categorized
  DynamoDB failures, plus latency and item-size distributions.
- **OBS-004**: Telemetry must not contain raw idempotency keys or digests, raw
  DynamoDB keys, request/response bodies, snapshots, model artifacts, AWS
  request IDs, credentials, or provider exception text. Game IDs may only be
  included under the repository's existing identifier/privacy policy.
- **OBS-005**: Telemetry emission failure must not change repository results,
  trigger a retry, or make a committed operation appear unsuccessful.

### 3.3 Deployment and rollback

- **OPS-001**: Document a staged cutover runbook that verifies infrastructure,
  IAM, startup validation, readiness, logs/metrics, and a disposable game flow
  before increasing traffic. Backend configuration and task rollout must be
  coordinated; mixed authoritative stores must not receive game traffic.
- **OPS-002**: Cutover gates are: increments 3.7–3.9 deployed, table backup/PITR
  enabled, TTL checked, least-privilege IAM verified, integration suites passed,
  alarms/dashboards available, and a tested rollback target recorded.
- **OPS-003**: Stop or roll back when startup/readiness fails, persistence-
  unavailable or unresolved-result rates breach the documented threshold,
  item sizes threaten the budget, or cross-instance/retry probes violate their
  contracts. Threshold owners and observation windows must be stated in the
  runbook rather than embedded in application code.
- **OPS-004**: Rollback must drain or stop affected traffic before changing
  repository mode. Rolling back to memory forfeits access to games created or
  changed in DynamoDB and is allowed only with explicit incident-owner
  acceptance. Do not copy, shadow-write, or automatically reconcile data.
- **OPS-005**: Record deployment time, configuration, table, application
  version, verification results, rollback decision, and responsible operator,
  without recording sensitive payloads or keys.

- **CON-001**: Do not modify `battle_hexes_core`, public HTTP schemas, command
  semantics, persistence item formats, retention rules, or frontend behavior.
- **CON-002**: Do not add a fallback, dual-write, cache, scan, migration, purge
  worker, or automatic retry of game behavior.
- **GUD-001**: Keep telemetry decoration separate from repository correctness
  logic and keep deployment procedures in an operator-facing runbook.

## 4. Interfaces & Data Contracts

### 4.1 Composition contract

| Validated mode | Selected repository | AWS access | Fallback |
| --- | --- | --- | --- |
| Disabled | `GameRepositoryInMemory` | None | Not applicable |
| Enabled | `GameRepositoryDynamoDB` | Required | Forbidden |

Selection occurs once per lifespan. All command-service instances in that
process receive the selected repository.

### 4.2 Telemetry contract

```text
repository_operation_completed {
  repository, operation, outcome, latency_ms,
  game_version?, game_item_bytes?, receipt_item_bytes?,
  dynamodb_error_category?
}
```

Fields marked `?` are omitted when unknown or inapplicable. Labels must be
bounded; item sizes and latency are numeric measurements, not metric labels.
The instrumentation backend is implementation-defined and must be injectable in
tests.

### 4.3 Operational artifacts

The cutover runbook must define prerequisites, staged rollout steps, smoke-test
commands, metric/log queries, thresholds and observation windows, stop/rollback
authority, rollback steps, and post-cutover verification. It must explicitly
state that rollback does not preserve DynamoDB-backed sessions in memory mode.

## 5. Acceptance Criteria

- **AC-001**: Given enabled mode, every game request across two API processes
  observes the same DynamoDB state; restarting either process loses no committed
  game or receipt, and no in-memory repository is constructed or accessed.
- **AC-002**: Given disabled mode without AWS credentials, startup and all game
  flows use only memory and remain ready without AWS access.
- **AC-003**: Two distinct commands racing from version N yield exactly one
  committed version N+1 and one version conflict with no orphan receipt.
  Concurrent identical commands yield one transition and identical responses.
- **AC-004**: When a committed write response is lost, retrying the same request
  returns the stored receipt without rerunning authoritative game behavior. An
  unresolved result returns 503 and does not fall back.
- **AC-005**: At `ttl == now`, games and receipts are logically absent even if
  physically present; GET/replay does not extend retention, while a successful
  unique mutation does.
- **AC-006**: Realistic growing combat, defensive-fire, and reinforcement
  histories remain complete near the safe budget, expose item-size telemetry,
  and fail before writing when either item exceeds the budget.
- **AC-007**: Every repository outcome emits the required bounded telemetry;
  inspection confirms prohibited data is absent and telemetry failure does not
  alter the public outcome.
- **AC-008**: A staged deployment executes the runbook gates and smoke tests,
  and a rehearsal demonstrates traffic drain plus rollback without automatic
  memory fallback or claims of session continuity.

## 6. Test Automation Strategy

- Add composition tests for one-time selection, dependency injection, no AWS
  construction in memory mode, and no fallback after DynamoDB failures.
- Run the shared repository contract and multi-client integration suites against
  a disposable compatible table. Use separate repository/application instances
  for restart, cross-instance, race, lost-response, expiry, and near-budget
  history cases; clean up only test-owned keys.
- Inject a telemetry sink/clock to assert event fields, bounded categories,
  latency/size measurements, redaction, and best-effort emission without
  coupling tests to exact log prose.
- Run `./server-side-checks.sh`, `npm test` in `battle-hexes-web`, and
  `./cloudformation-checks.sh`. Execute repository integration and deployment
  smoke checks in an environment with a real or compatible DynamoDB service;
  mocks alone cannot prove concurrency or durability.

## 7. Implementation Sequence & Activation

1. Add storage-neutral instrumentation around both repositories and validate
   redaction without changing selection.
2. Wire one-time lifespan selection from the increment 3.9 configuration and
   prove disabled-mode isolation plus enabled-mode no-fallback behavior.
3. Add multi-instance integration and failure-injection coverage.
4. Publish dashboards/alarms and the cutover/rollback runbook; rehearse it in a
   non-production environment.
5. Deploy backend prerequisites, enable DynamoDB for staged traffic, execute
   verification, observe the documented window, then complete or roll back.

Steps 1, 3, and runbook drafting may proceed in parallel after increments
3.7–3.9. Production activation may occur only after all acceptance gates pass.

## 8. Rationale & Context

One-time selection prevents requests within a process from crossing storage
domains. Atomic transactions and receipt-first reconciliation make durability,
concurrency, and retry behavior observable across processes. A deliberate
rollback warning is necessary because memory cannot contain sessions committed
to DynamoDB. Bounded, payload-free telemetry supports diagnosis without
creating a sensitive-data or metric-cardinality hazard.

## 9. Dependencies & External Integrations

- **DEP-001**: Increments 3.7–3.9 provide the active HTTP flow, DynamoDB adapter,
  validated configuration, readiness, table, and IAM contracts.
- **DEP-002**: DynamoDB supplies strongly consistent reads, transactional
  conditional writes, TTL cleanup, encryption, and point-in-time recovery.
- **DEP-003**: The deployment platform must support staged task replacement,
  traffic draining, configuration rollback, and centralized metrics/logs.
- **DEP-004**: [`docs/design.md`](../../docs/design.md), sections 1.4, 1.7–1.9,
  1.11–1.12, and 1.14–1.17, remains authoritative where this spec is silent.

## 10. Examples & Edge Cases

| Situation | Required result |
| --- | --- |
| Enabled startup cannot describe the table | Startup fails; memory is never selected. |
| DynamoDB becomes unavailable after startup | `/ready` is 503; `/health` remains 200; game operations fail storage-neutrally. |
| Transaction commits and client observes a timeout | Strong receipt reconciliation or same-key retry returns the committed response. |
| Metrics backend is unavailable | Repository result is unchanged; telemetry loss follows platform policy. |
| Near-budget game but oversized receipt | Entire transaction is rejected; prior version remains authoritative. |
| Rollback requested with active DynamoDB games | Drain traffic and obtain explicit data-continuity acceptance before disabling DynamoDB. |

## 11. Validation Criteria

The increment is complete when all acceptance criteria have automated evidence
where feasible, full server/frontend/infrastructure checks pass, compatible-
DynamoDB tests prove cross-process authority and race/retry behavior, telemetry
and alarms are observable without prohibited data, and the cutover and rollback
runbook has been successfully rehearsed and recorded.

## 12. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.10.
- [In-memory end-to-end activation](design-in-memory-end-to-end-activation.md).
- [DynamoDB repository](design-dynamodb-repository.md).
- [Infrastructure and readiness preparation](infrastructure-readiness-preparation.md).
- [Application persistence design](../../docs/design.md).

## 13. Open Questions

No questions.
