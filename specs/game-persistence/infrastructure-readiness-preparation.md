---
title: Infrastructure and Readiness Preparation
version: 1.0
date_created: 2026-09-26
last_updated: 2026-09-26
tags: [infrastructure, game-persistence, api, dynamodb, readiness]
---

# Introduction

This specification defines increment 3.9 of the game-persistence schedule. It
prepares DynamoDB infrastructure, least-privilege access, configuration
validation, and readiness reporting without making DynamoDB authoritative.

## 1. Purpose & Scope

Prepare `battle_hexes_api` and its CloudFormation templates for a safe DynamoDB
cutover. This increment validates configuration at startup and makes `/ready`
verify the configured table contract when DynamoDB mode is enabled.

In scope are API configuration, readiness checks, task-role permissions,
development-table compatibility, CloudFormation lint coverage, and focused
tests. Out of scope are repository selection, route changes, table migration or
creation by the API, telemetry beyond readiness diagnostics, and the production
cutover in increment 3.10. `/health` behavior must not change.

## 2. Definitions

| Term | Definition |
| --- | --- |
| DynamoDB mode | Configuration where `DYNAMODB_ENABLED` is exactly `true` after case and surrounding-whitespace normalization. |
| Liveness | Evidence that the API process can serve requests; exposed by `/health`. |
| Readiness | Evidence that the process and its configured external dependencies can serve application traffic; exposed by `/ready`. |
| Table contract | An active DynamoDB table with string partition key `pk`, string sort key `sk`, and enabled TTL on attribute `ttl`. |
| TTL | DynamoDB Time to Live, used for asynchronous physical deletion of expired items. |

## 3. Requirements, Constraints & Guidelines

### 3.1 Configuration and startup

- **REQ-001**: Parse `DYNAMODB_ENABLED` once during application lifespan
  startup. Accept only `true` or `false`, case-insensitively and with surrounding
  whitespace ignored. Default an absent value to `false`; all other values must
  fail startup with a configuration error.
- **REQ-002**: Trim `DDB_TABLE_NAME`. DynamoDB mode requires a non-empty value;
  absence or whitespace-only content must fail startup. In-memory mode must not
  require this variable or contact AWS.
- **REQ-003**: Store one validated immutable configuration object in application
  composition and use it for readiness and, in increment 3.10, repository
  selection. Do not independently reparse environment variables in those
  components.
- **REQ-004**: Invalid configuration must prevent startup. AWS unavailability or
  a nonconforming table must make `/ready` return not-ready; neither condition
  may silently select or fall back to the in-memory repository.

### 3.2 Readiness behavior

- **REQ-005**: `/health` must always remain independent of DynamoDB and return
  its existing success response while the API process is running.
- **REQ-006**: `/ready` in in-memory mode must return its existing success
  response without constructing an AWS client or making an AWS call.
- **REQ-007**: Each `/ready` evaluation in DynamoDB mode must use
  `DescribeTable` to require `TableStatus == "ACTIVE"` and verify exactly one
  HASH key named `pk` and one RANGE key named `sk`; both attributes must have
  DynamoDB type `S`. Additional non-key attribute definitions do not satisfy or
  invalidate this contract.
- **REQ-008**: DynamoDB readiness must also call `DescribeTimeToLive` and require
  `TimeToLiveStatus == "ENABLED"` with `AttributeName == "ttl"`. `ENABLING`,
  `DISABLING`, `DISABLED`, missing, or malformed responses are not ready.
- **REQ-009**: Missing tables, access denial, throttling, endpoint failures,
  malformed AWS responses, and other boto client/core failures must make
  `/ready` return HTTP 503 with the existing generic public body. Provider
  details may be logged but must not be returned to clients.
- **REQ-010**: Readiness must use an injected DynamoDB client or client factory
  so unit tests do not require AWS. Keep configuration parsing, table-contract
  evaluation, and HTTP translation independently testable.
- **REQ-011**: At the increment 3.10 cutover, DynamoDB-mode composition must
  additionally require that the selected repository is the DynamoDB adapter.
  This increment may establish that check or interface, but must not activate
  DynamoDB repository selection itself.

### 3.3 Infrastructure and IAM

- **REQ-012**: The managed table must retain on-demand billing, server-side
  encryption, point-in-time recovery, string `pk`/`sk` keys, and TTL enabled on
  `ttl`. Do not add indexes, streams, or another table for persistence.
- **REQ-013**: The API task role must grant only `dynamodb:GetItem`,
  `dynamodb:PutItem`, `dynamodb:UpdateItem`, `dynamodb:DescribeTable`, and
  `dynamodb:DescribeTimeToLive` for the configured table. Do not grant Scan,
  Query, batch, stream, index, delete, or wildcard DynamoDB data access.
- **REQ-014**: Do not add a `dynamodb:TransactWriteItems` action; DynamoDB
  transaction authorization is derived from the underlying item actions.
- **REQ-015**: Remove index ARNs from the task-role resources because this
  design has no index operation. Scope table data actions to the imported table
  ARN. If AWS requires a different resource scope for a describe action,
  isolate only that action in the narrowest valid statement and document it.
- **REQ-016**: Keep every repository CloudFormation template listed in
  `cloudformation-checks.sh`. Any changed template and the canonical script must
  pass `cfn-lint --non-zero-exit-code error`.

- **CON-001**: Do not modify `battle_hexes_core`, the frontend, game routes, the
  persistence HTTP contract, or repository semantics.
- **CON-002**: Do not probe DynamoDB from `/health`, create or mutate tables at
  API startup, or treat DynamoDB TTL's asynchronous deletion as readiness.
- **GUD-001**: Log readiness failures by category and table name only; never log
  raw idempotency keys, snapshots, receipts, or response bodies.

## 4. Interfaces & Data Contracts

### 4.1 Environment contract

| `DYNAMODB_ENABLED` | `DDB_TABLE_NAME` | Startup | `/ready` dependency |
| --- | --- | --- | --- |
| absent or `false` | absent | succeeds | none |
| `false` | present | succeeds; may warn that it is unused | none |
| `true` | nonblank | succeeds | table contract |
| `true` | absent/blank | fails | not applicable |
| any other value | any | fails | not applicable |

### 4.2 Endpoint contract

| Endpoint | Ready result | Dependency failure result |
| --- | --- | --- |
| `GET /health` | `200 {"status":"ok"}` | Not applicable; no AWS access |
| `GET /ready` | `200 {"status":"ready"}` | `503 {"detail":"Service not ready"}` |

### 4.3 AWS calls

```text
DescribeTable(TableName=<validated DDB_TABLE_NAME>)
DescribeTimeToLive(TableName=<validated DDB_TABLE_NAME>)
```

Readiness is true only when both responses satisfy REQ-007 and REQ-008. It must
not use data-plane reads, scans, writes, or a known item as a readiness probe.

## 5. Acceptance Criteria

- **AC-001**: Given in-memory mode and unavailable AWS credentials, when the
  application starts and `/ready` is called, then startup and readiness succeed
  without constructing an AWS client.
- **AC-002**: Given invalid `DYNAMODB_ENABLED` or enabled mode without a table
  name, when lifespan starts, then startup fails and no repository fallback or
  AWS request occurs.
- **AC-003**: Given DynamoDB mode and an active table with the required string
  keys and enabled `ttl`, when `/ready` is called, then it returns HTTP 200.
- **AC-004**: Given an inactive or unavailable table, wrong/missing/extra key,
  non-string key, disabled/transitional TTL, wrong TTL attribute, malformed
  response, or missing permission, when `/ready` is called, then it returns HTTP
  503 with no provider detail in the response.
- **AC-005**: Given any DynamoDB readiness failure, when `/health` is called,
  then it still returns its existing HTTP 200 response without an AWS call.
- **AC-006**: The task role contains only the DynamoDB actions and table
  resource scopes in REQ-013 through REQ-015; repository transactions remain
  authorized through `PutItem` and `UpdateItem`.
- **AC-007**: The development table and any newly managed environment table
  satisfy the table contract, and all repository templates are included in and
  pass the canonical CloudFormation check.
- **AC-008**: Runtime game repository selection and all game endpoint behavior
  remain unchanged until increment 3.10.

## 6. Test Automation Strategy

- Add configuration tests for defaults, normalized booleans, invalid values,
  blank table names, and disabled mode with an unused table name.
- Use botocore stubs or injected fakes to test active/inactive status, every key
  schema/type mismatch, TTL statuses and attribute mismatch, malformed
  responses, not-found, access-denied, and endpoint failures.
- Assert endpoint status and stable public bodies, client-call parameters, and
  absence of AWS client construction in `/health` and in-memory readiness.
- Run existing API tests through `./server-side-checks.sh` and infrastructure
  validation through `./cloudformation-checks.sh`. No live AWS test or new
  coverage threshold is required for this increment.

## 7. Rationale & Context

Separating liveness from readiness keeps the process observable during an AWS
incident while preventing the load balancer from sending game traffic to an
instance whose configured persistence dependency is unusable. Exact schema and
TTL checks detect a reachable but incompatible table before DynamoDB becomes
authoritative. Least-privilege IAM reflects the repository's actual GetItem and
transactional put/update operations.

## 8. Dependencies & External Integrations

- **DEP-001**: Increment 3.8 defines the DynamoDB adapter's concrete calls and
  confirms the required item actions.
- **DEP-002**: AWS DynamoDB supplies table and TTL descriptions; the ECS task
  role supplies runtime credentials.
- **DEP-003**: `battle_hexes_api/dev-database.yml` supplies the development
  table, and `battle_hexes_api/ecs-backend.yml` supplies API configuration,
  least-privilege IAM, and the `/ready` load-balancer probe.
- **DEP-004**: [`docs/design.md`](../../docs/design.md), sections 1.9, 1.14,
  1.16, and 1.17, remains authoritative where this specification is silent.
- **DEP-005**: Increment 3.10 consumes the validated configuration and readiness
  contract when it activates DynamoDB repository selection.

## 9. Examples & Edge Cases

| Situation | Required outcome |
| --- | --- |
| Table is `UPDATING`, but schema and TTL are valid | Not ready |
| Keys are `pk`/`sk`, but `sk` is numeric | Not ready |
| TTL is `ENABLING` on `ttl` | Not ready until status is `ENABLED` |
| TTL is `ENABLED` on `expires_at` | Not ready |
| `DescribeTable` succeeds; TTL permission is denied | Not ready; `/health` remains healthy |
| DynamoDB disabled; stale table name is present | Ready without AWS access; warning is permitted |

## 10. Validation Criteria

The increment is complete when configuration and readiness tests cover all
acceptance cases, API checks pass, CloudFormation lint passes, task-role review
finds no unused DynamoDB permissions or index resource, the canonical lint list
contains every repository template, and DynamoDB remains unselected at runtime.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.9.
- [DynamoDB repository](design-dynamodb-repository.md).
- [In-memory end-to-end activation](design-in-memory-end-to-end-activation.md).
- [Application persistence design](../../docs/design.md).

## 12. Open Questions

No questions.
