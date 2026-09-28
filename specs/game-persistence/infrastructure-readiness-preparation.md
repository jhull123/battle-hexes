---
title: Infrastructure and Readiness Preparation
version: 1.0
date_created: 2026-09-26
last_updated: 2026-09-28
tags: [infrastructure, game-persistence, api, dynamodb, readiness]
---

# Introduction

This specification defines increment 3.9 of the game-persistence schedule. It
prepares DynamoDB infrastructure, least-privilege access, configuration
validation, and readiness reporting without making DynamoDB authoritative.

## 1. Purpose & Scope

Prepare `battle_hexes_api` and its CloudFormation templates for a safe DynamoDB
cutover. This increment validates configuration and static table invariants at
startup. `/ready` reports process-local completion of that startup work.

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
| Readiness | Evidence that application startup completed; exposed by `/ready` without a per-probe AWS call. |
| Table contract | String partition key `pk`, string sort key `sk`, and TTL enabled on attribute `ttl`. Key compatibility gates startup; TTL is an operational warning. |
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
  composition for increment 3.10 repository selection. Do not independently
  reparse environment variables in other components.
- **REQ-004**: Invalid configuration, an incompatible table key schema, an
  unavailable table, or failure to verify the table at startup must prevent
  startup. None may silently select or fall back to memory. Treat `ACTIVE` and
  `UPDATING` as usable table statuses.
- **REQ-004a**: At startup, check TTL status and attribute. Warn if TTL is not
  enabled on `ttl` or cannot be verified, but do not reject traffic: logical
  expiry is enforced by the repository, and TTL performs eventual cleanup.
  Keep startup checks outside `readiness.py`.

### 3.2 Readiness behavior

- **REQ-005**: `/health` must always remain independent of DynamoDB and return
  its existing success response while the API process is running.
- **REQ-006**: `/ready` must return its existing success response after startup
  completes in either mode, without constructing an AWS client or making an AWS
  call on each probe.
- **REQ-007**: Startup must verify exactly one HASH key named `pk` and one
  RANGE key named `sk`, both DynamoDB type `S`. Additional non-key attribute
  definitions do not invalidate this contract.
- **REQ-008**: No `/ready` evaluation may call DynamoDB. Startup owns table
  status, schema, and TTL checks; later DynamoDB failures are handled by
  repository operations and operational monitoring.
- **REQ-009**: Missing tables, access denial, throttling, endpoint failures,
  malformed AWS responses, and other boto client/core failures during required
  table startup validation must prevent startup without exposing provider
  details in the raised application error.
- **REQ-010**: Startup validation must accept an injected DynamoDB client
  factory so unit tests do not require AWS. Keep configuration parsing and
  startup validation independently testable.
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
- **GUD-001**: Log startup warnings by category and table name only; never log
  raw idempotency keys, snapshots, receipts, or response bodies.

## 4. Interfaces & Data Contracts

### 4.1 Environment contract

| `DYNAMODB_ENABLED` | `DDB_TABLE_NAME` | Startup | `/ready` dependency |
| --- | --- | --- | --- |
| absent or `false` | absent | succeeds | none |
| `false` | present | succeeds; may warn that it is unused | none |
| `true` | nonblank | succeeds if table is usable and keys are compatible; warns for TTL mismatch | none after startup |
| `true` | absent/blank | fails | not applicable |
| any other value | any | fails | not applicable |

### 4.2 Endpoint contract

| Endpoint | Success result | AWS dependency behavior |
| --- | --- | --- |
| `GET /health` | `200 {"status":"ok"}` | Not applicable; no AWS access |
| `GET /ready` | `200 {"status":"ready"}` | No AWS call; startup failure prevents serving |

### 4.3 AWS calls

```text
Startup: DescribeTable(TableName=<validated DDB_TABLE_NAME>)
Startup: DescribeTimeToLive(TableName=<validated DDB_TABLE_NAME>)
```

Startup rejects an unavailable table or incompatible/unverified keys and warns
for TTL mismatch. `/ready` makes no AWS call. Startup uses no data-plane read,
scan, write, or known item as a probe.

## 5. Acceptance Criteria

- **AC-001**: Given in-memory mode and unavailable AWS credentials, when the
  application starts and `/ready` is called, then startup and readiness succeed
  without constructing an AWS client.
- **AC-002**: Given invalid `DYNAMODB_ENABLED` or enabled mode without a table
  name, when lifespan starts, then startup fails and no repository fallback or
  AWS request occurs.
- **AC-003**: Given DynamoDB mode and the required string keys, startup
  succeeds for an `ACTIVE` or `UPDATING` table. `/ready` then returns HTTP 200
  without contacting AWS.
- **AC-004**: Wrong/missing/extra or non-string keys fail startup. Disabled or
  transitional TTL, wrong TTL attribute, and failed TTL verification warn at
  startup but do not block serving. An unavailable table or failed
  `DescribeTable` call prevents startup without provider detail.
- **AC-005**: Given a later DynamoDB failure, `/health` and `/ready` remain
  independent of AWS; repository operations report the failure.
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
- Use injected fakes to test startup key mismatches, usable/unavailable statuses,
  provider errors, and TTL warnings.
- Assert endpoint status and stable public bodies, client-call parameters, and
  absence of AWS calls from both `/health` and `/ready` after startup.
- Run existing API tests through `./server-side-checks.sh` and infrastructure
  validation through `./cloudformation-checks.sh`. No live AWS test or new
  coverage threshold is required for this increment.

## 7. Rationale & Context

Startup rejects a misconfigured or unavailable table before an instance serves
traffic. Once running, a shared DynamoDB failure cannot be fixed by ALB routing
between API tasks; probing DynamoDB from every target adds control-plane calls
without providing a healthy alternative. Repository operations surface later
failures. TTL only purges records asynchronously; repository conditions enforce
logical expiry. A TTL mismatch requires operational attention, not ALB
deregistration. Least-privilege IAM reflects actual item operations.

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
| Table is `UPDATING` with compatible keys | Startup succeeds; ready |
| Table is `CREATING` | Startup fails |
| Keys are `pk`/`sk`, but `sk` is numeric | Startup fails |
| TTL is `ENABLING` on `ttl` | Startup warns; readiness can succeed |
| TTL is `ENABLED` on `expires_at` | Startup warns; readiness can succeed |
| `DescribeTable` succeeds; TTL permission is denied | Startup warns; readiness can succeed |
| DynamoDB fails after startup | Repository operations fail; `/ready` makes no AWS call |
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
