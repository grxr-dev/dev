# Inbox V1 synchronized one-attempt recovery

**PARTIAL deployment; implementation and167 tests PASS.** Source installed in the Windows bridge, but the running bridge still has the old queue/listener. A single tray **Restart Bridge** is strictly required after this task returns. No hot reload exists; the current new-admin-route GET returns404 and its startup token does not exist. No restart, recovery authorization, fresh delivery attempt or cursor change was performed.

## Exact scope and authorization

Only this existing identity is accepted:
`brainage-task-aw5-20261015-01:52508ca28d2650562bee990b9780e050cfbab9a3a3854699bfd05dc74d391bf4`

Stored canonical wrapper/payload SHA256 is pinned to `4a4270b65d7f6b55968d7352c74d166074eec02822cd69a88a4651237687778b` (different from the result hash in the delivery ID). Requires FAILED_PERMANENT, count3, exhausted pre-Send error, and a prior proven pre_send FAILED_RETRYABLE outcome. DELIVERED/NEEDS_REVIEW/other IDs or payloads cannot be rearmed.

Administrative GET/POST `/local/inbox/admin/recovery-once` exists only on127.0.0.1:18741. Existing loopback/Host/Origin/Referer/header gates remain; an additional random local `X-Jarvis-Admin` token is required even for status. Startup creates `.runtime/inbox_recovery_admin.token`; it is never given to Firefox/native host or published. Public bridge GET/POST recovery paths remain404. No new remote bearer endpoint or general RPC.

## Atomic, synchronized state machine

The authoritative queue RLock covers compare-and-swap fingerprint validation, readiness check, history capture, authorization, diagnostic-hold release and arming. The fingerprint covers the entire in-memory queue and recovery ledger. Any other queued/retryable/in-flight work rejects authorization. A second authorization, including concurrent/re-entrant calls or later attempts, is refused permanently for this one-use operation.

A `recovery_once` object is added to the same atomically replaced/fsynced queue JSON only when used. It records the complete original terminal entry (including old token/outcome/timestamps/text/hash/count), all available matching rolling/retained trace records with source hashes, authorization identity/readiness, and ordered authorization/arm/claim/outcome audit events. No existing trace/history is deleted or rewritten. Up to8MiB of evidence sources are scanned; malformed/oversized evidence rejects authorization, not truncates it. Private runtime evidence is not committed.

`PREPARED` is durable before releasing the no-send hold and cannot be claimed. The matching request is atomically renamed to `inbox_recovery_readiness_authorized.json`; no queue file is edited outside the bridge. `ARMED` becomes durable next. A failed second commit restores the original terminal entry with a CANCELLED recovery audit; if persistence also fails, PREPARED remains unclaimable. Duplicate recovery is still rejected.

Readiness must come from the current native-validated no-send probe, match the fixed conversation and exact one non-hidden/non-discarded/non-private tab, have reachable/bound script and present/empty composer, no busy generation/delivery, and be no older than60 seconds (future skew at most5 seconds). Probe nonce and complete armed-entry fingerprint are rechecked at claim. Normal background/content unique-tab, draft, exact text/hash, UUID and Send verification remain unchanged and authoritative immediately before Send.

The original attempt count is **not reset**. It stays3 through authorization and becomes4 on the single normal claim. Claim token changes normally, with a token hash in the recovery claim audit. Claim and audit persist atomically. Any extra attempt failure is terminal; proven pre-Send failure at count4 cannot schedule another retry. DELIVERED still requires normal exact-hash/one-Send/new-UUID/composer proof. No forced success or cursor endpoint is introduced. Existing idempotent ACK semantics remain.

A restart while PREPARED/ARMED cancels unclaimed recovery; a crash after claim becomes NEEDS_REVIEW and never resends. Ordinary version2 queue files and three-attempt behavior remain unchanged when unused. The optional recovery ledger extends version2's top-level schema; the local enable validator is updated. Older queue code intentionally rejects this extended schema rather than discarding its audit. Do not roll back to old code after use by dropping history.

## Activation and one authorized attempt

Only required user action: **tray -> Restart Bridge** after this task has returned. No Firefox/native-host reload, tray troubleshooting, token editing or binding change is requested. The readiness hold is preserved and all deliveries are terminal; loading these files does not itself authorize a recovery.

After restart, the existing native poll can refresh the no-send probe without Firefox user action:

```powershell
python bridge/inbox-v1/recover_once.py --refresh-readiness
python bridge/inbox-v1/readiness_probe.py
python bridge/inbox-v1/recover_once.py
```

Wait for the newly requested exact nonce to return READY. Read the administrative status once and review its `queue_fingerprint`, target, prior count and readiness. If any check fails/stales, STOP; no reset/guess/retry loop.

Then, only under the existing explicit one-attempt authorization:

```powershell
python bridge/inbox-v1/recover_once.py --recover-once --expected-fingerprint <reviewed-fingerprint>
```

That single POST authorizes the single next normal frontend delivery; it does not directly call Send. Observe read-only status/queue/trace until normal terminal outcome. Do not repost the authorization after a timeout: inspect status first. Do not force a cursor; Jarvis can advance only under its existing actual-DELIVERED contract. This CLI has no automatic recovery or delivery retry loop.

## Validation and artifacts

31 focused queue/HTTP tests cover correct recovery, wrong identity/hash/state, ambiguous terminal, duplicate/concurrent calls, stale fingerprints before/after authorization, another pending delivery, fresh/bad/stale readiness and claim-time recheck, one-extra-attempt budget, exact full history and prior-trace capture, idempotent ACK, crashes before/after claim, disk/hold-release failures, authenticated local route and Origin rejection. Plus136 existing/focused regressions:49 content,10 background,14 readiness JS,9 readiness native,21 queue,9 native,4 trace,12 incident retention,2 rollback,6 legacy HTTP/public-route checks. All167 pass. The existing fixed-port native-EXE smoke is excluded to avoid rebinding/stopping production18741; HTTP uses ephemeral fixture ports. Fixture Send/DELIVERED proof is synthetic, not a production smoke claim.

Production files and source-only deployment manifest are under `production/`. `deploy.py` validates all normalized baseline/new hashes before changes, backs up old source, and stages only code/tests. It does not start/restart/recover or access queue state. Backup for this deployment: `bridge/backups/recovery-once-20261015-200753` (queue/listener); manage.py changes only its optional-ledger validation. Tests: `python bridge/inbox-v1/tests/test_recovery_once.py`.

Current seq94 remains FAILED_PERMANENT, count3, last_attempt_at1792052662.818595. No recovery ledger exists in the production queue. Queue counts:34 DELIVERED,3 FAILED_PERMANENT,27 NEEDS_REVIEW. Local cursor is not modified; Jarvis VM cursor is not accessible. Existing readiness is stale, so no actual attempt is permitted now. See RESULT.json. No Brain Age code/state, outbound GitHub behavior, retired courier, or Linux watcher changes.
