# DynamoDB cutover and rollback runbook

This procedure changes the API's single authoritative repository. It does not
copy, reconcile, cache, or shadow-write games between repositories. Never send
game traffic to a deployment containing a mixture of in-memory and DynamoDB
tasks.

## Ownership and change record

The release operator owns the rollout; the incident commander owns every stop
or rollback decision. Before starting, record the operator, incident commander,
UTC deployment time, application image/version, target environment and table,
`DYNAMODB_ENABLED` value, tested rollback image/configuration, and links to the
verification evidence. Do not record game bodies, idempotency values or hashes,
DynamoDB keys, AWS request IDs, credentials, or provider error text.

The incident commander must set and record, for this environment, the alert
thresholds and observation windows for persistence unavailability, unresolved
results, throttling, item-size percentiles, and latency. Thresholds belong in
the deployment/change record and alarm configuration—not application code.

## Prerequisite gates

Do not begin until all boxes have objective evidence:

- [ ] Persistence increments 3.7 through 3.9 are deployed.
- [ ] The target table has point-in-time recovery/backups and encryption on.
- [ ] TTL is enabled on `ttl`; `pk` and `sk` are string keys.
- [ ] The task role is least privilege: `DescribeTable`,
  `DescribeTimeToLive`, `GetItem`, `PutItem`, and `UpdateItem` only as required.
  `TransactWriteItems` uses the permissions for its underlying `Put` and
  `Update` actions; it has no separate IAM action to grant.
- [ ] Server, compatible-DynamoDB integration, and infrastructure suites pass.
- [ ] Repository latency/size distributions and bounded outcome/error counters
  are visible; the agreed alarms are enabled.
- [ ] The previous image and its exact configuration have passed a rollback
  rehearsal, including traffic drain.

## Staged cutover

1. Stop game traffic or direct it away from the deployment. Confirm no old task
   is serving game requests before repository mode changes.
2. Deploy a zero-traffic canary with `DYNAMODB_ENABLED=true` and the recorded
   `DDB_TABLE_NAME`. Confirm startup validates the table and `/health` is 200.
3. Confirm `/ready` is 200 and the logs identify DynamoDB as enabled. Check that
   there are no access/configuration, endpoint/network, service, throttling,
   malformed-data, or unresolved/unknown repository failures.
4. With a unique disposable idempotency key, create a disposable game, GET it,
   issue one valid versioned command, repeat that exact command, and confirm the
   replay is byte-identical and does not advance the version. Never paste the
   key or response into the change record.
5. Restart/replace the canary and GET the disposable game. From a second task,
   repeat GET and replay checks. Run the approved two-writer race probe and
   confirm one N+1 commit plus one version conflict; run the lost-response probe
   and confirm receipt reconciliation or a 503, never memory fallback.
6. Increase traffic by the platform's staged increments. At every increment,
   observe for the recorded window and review readiness, repository outcomes,
   DynamoDB error categories, latency, and game/receipt item-size percentiles.
7. After full replacement, verify no in-memory-configured task remains, repeat
   the cross-task disposable flow, and record results and dashboard links.

Example non-sensitive probes (substitute approved host and disposable IDs):

```sh
curl --fail --silent --show-error "$API/health"
curl --fail --silent --show-error "$API/ready"
aws dynamodb describe-table --table-name "$DDB_TABLE_NAME" \
  --query 'Table.{Status:TableStatus,Keys:KeySchema}'
aws dynamodb describe-continuous-backups --table-name "$DDB_TABLE_NAME" \
  --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'
aws dynamodb describe-time-to-live --table-name "$DDB_TABLE_NAME"
```

Confirm the point-in-time recovery status is `ENABLED`. Run the backup probe
with an operator role; the API task role does not need backup-inspection access.

Use centralized logs/metrics to group `repository_operation_completed` by
`repository`, `operation`, `outcome`, and `dynamodb_error_category`; graph
`latency_ms`, `game_item_bytes`, and `receipt_item_bytes` as distributions.

## Stop conditions

Stop increasing traffic and notify the incident commander when startup or
readiness fails, an agreed persistence-unavailable/unresolved threshold is
breached, sizes approach the 358,400-byte safe budget, telemetry disappears,
or any cross-instance, restart, race, retry, expiry, or replay probe violates
its contract. The incident commander decides whether to hold, repair forward,
or roll back using the recorded window and thresholds.

## Rollback

1. Drain or stop all affected game traffic. Confirm requests cannot reach a
   mixed set of authoritative stores.
2. Prefer rolling back application code while retaining DynamoDB mode when the
   recorded target supports it.
3. Before changing to `DYNAMODB_ENABLED=false`, the incident commander must
   explicitly accept that **memory mode cannot access or preserve any game
   created or changed in DynamoDB**. Record that acceptance and customer impact.
4. Deploy the recorded image and configuration as one coordinated replacement;
   do not copy, dual-write, reconcile, or automatically fall back.
5. Verify all old tasks are drained, `/health` and `/ready` pass, and a new
   disposable flow works in the selected store. Record timings, configuration,
   verification results, decision, and responsible operator.

## Post-cutover verification

For the incident commander's full observation window, continue reviewing
alarms, bounded failures, conflict/replay rates, expiry behavior, latency and
item-size headroom. Preserve the non-sensitive deployment record and remove
only test-owned disposable data according to the approved cleanup procedure.
