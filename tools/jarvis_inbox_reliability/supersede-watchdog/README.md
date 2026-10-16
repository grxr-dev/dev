# One stale watchdog supersession

**PARTIAL activation; implementation and158 tests PASS.** Production source is staged. The running bridge returns404 for the new route; no cancellation has occurred. A managed bridge restart at an idle boundary is required to load the changed queue/listener. No restart was performed while this task was active. This does not gate Brain Age task submission, completion ingestion or project work.

## Narrow owner policy

Only `jarvis-continuity-watchdog:1fe09e7e9c1dec11d6dbd2385e0fb9cb8697ab85ede379f0308cd467b361ec52` can be cancelled. It must still be QUEUED, attempt_count0, no claim token, no attempt timestamp, no delivered timestamp, no retry schedule/error and no outcome. Its complete canonical text must hash to the ID suffix. A concurrent/stale queue fingerprint, prior disposition or active seq94 recovery fails closed. Other entries are neither selected nor changed.

Supersession is mechanically verified with fixed repository `grxr-dev/codex-relay`, GitHub credential actor/private-repo checks, exact issue numbers70/74/76/78, author/title/envelope/request IDs, closed issue state and original local prompt hashes. A read-only SQLite transaction checks retained COMPLETED request/result records, source_ref/issue binding, result length, inner and ledger response hashes, exact commits and temporal/dependency order. The original nudge creation must be between AW10's issue close and AW11's creation. AW11/AW12/AW13 transport completion is sufficient: this policy does not assert each task was FULL PASS or authorize any further Brain Age task.

Pinned completed commits: AW10 c699e3a21207abaa72b8130bf54c0f189c846412; AW11 b10e83d9f5e236930d7b2fd8e1b2b301e978decc; AW12 b60203a9d30b3a8536395aaacdd15d126ee88399; AW13 1d64040633738bc63b5f49d2718d5c30dbad801c. Actual read-only proof SHA256: `0d967b5d98ae17649e89ef66554530af8d65904f73ce485adcdb132d4faadac6`.

## Synchronized disposition, not delivery

Loopback-only GET/POST `/local/inbox/admin/supersede-watchdog` reuses the separate local administrator token introduced by issue73. Native host/Firefox never receive that token. Existing loopback/Host/Origin/Referer checks remain. Public bridge routes remain404. No general cancellation API, URL, arbitrary target or project-state argument exists.

GET returns read-only proof and queue fingerprints. POST accepts exactly delivery_id, expected_fingerprint and expected_proof_sha256. Under the authoritative queue RLock it revalidates identity/state, fetches/validates the supersession evidence, compares the reviewed proof hash, and commits the record plus audit atomically. Network/SQLite/proof/persistence errors reject cancellation; no fallback or fuzzy verification.

For wire/schema compatibility the entry becomes FAILED_PERMANENT with last_error=`superseded watchdog; cancelled without delivery`, explicit outcome.state=`SUPERSEDED`, and a fresh administrative authorization ID. **It is not DELIVERED and no success proof is fabricated.** Attempt_count remains0; delivered_at, last_attempt_at and claim_token stay null. An optional top-level superseded_watchdog audit preserves the entire original entry, immutable evidence/hash, queue fingerprint, authorization ID/time and disposition. Both the existing recovery ledger and unrelated entries are preserved in the same fsynced/atomically replaced JSON. Duplicate/concurrent cancellation cannot create a second disposition. Startup validates the saved history and resulting entry without network calls. The local administrative enable validator accepts the optional audit. Older code intentionally rejects unknown audit schemas instead of discarding evidence; do not erase audits to downgrade.

Normal enqueue/claim/ACK behavior and queue JSON remain unchanged while this operation is unused. The diagnostic no-send hold stays in place, including after cancellation. There is no browser action, Send, seq94 recovery call, forced success, completion update, or cursor manipulation in this operation. Queue RLock/readonly WAL transaction are separate from the bridge's Codex turn and completion-write locks; no Brain Age runtime or project-state path is invoked.

## Deployment and activation

Production files staged: inbox_queue.py, inbox_local.py, new inbox_supersession.py, inbox-v1/manage.py, new inbox-v1/supersede_watchdog.py, focused tests. The interrupted attempt left partial queue/enable-validator edits; this clean retry detected and completed them before testing. Backup baseline: `bridge/backups/supersede-watchdog-20261015-230300/`. Source bundle/manifest/deploy helper are here. Deployment validates every source/baseline hash before any write, copies only code/tests, backs up changed files and never accesses queue/cursor state or restarts a process.

After a managed restart has loaded the new route, an authorized activation can review then cancel this exact item:

```powershell
python bridge/inbox-v1/supersede_watchdog.py
python bridge/inbox-v1/supersede_watchdog.py --supersede --expected-fingerprint <reviewed-queue-hash> --expected-proof-sha256 <reviewed-proof-hash>
```

Default is read-only. Explicit cancellation is one POST, no retry loop. After an ambiguous network response inspect status/history before any next action. This source-stage task did NOT execute that POST. No manual relay, browser action, token/registry/network troubleshooting or Brain Age pause is requested.

After cancellation, run the existing seq94 read-only queue preflight. The watchdog is currently its sole eligible blocker; tested cancellation removes only that eligibility. Actual production seq94 recovery remains blocked until cancellation is activated. Fresh no-send readiness is independently required for seq94. Do not recover seq94 in the cancellation task: it is a separate supported operation and is not atomically combined here.

## Validation and current state

158 final checks pass:26 supersession/provenance/history/concurrency/HTTP tests;31 recovery regression;21 ordinary queue;9 native;10 background;49 content;4 trace;2 rollback;6 existing HTTP/public-route isolation. Source fixtures use temporary queues/SQLite and FakeRPC/Mock GitHub. Initial test-only SQLite cleanup failures were fixed by closing fixture handles; final suite passes. One queue-test automatic approval timed out before execution; its one permitted retry passed. The fixed-port native EXE smoke is excluded rather than disturbing production18741; HTTP fixtures use ephemeral ports.

The actual GitHub/local read-only evidence check also passes. The production watchdog remains QUEUED/count0; no superseded audit exists. Seq94 remains FAILED_PERMANENT/count3. The latest queue preflight still identifies this watchdog as its sole eligible blocker. No source/history/cursor/Brain Age state was silently changed to manufacture cleanup. See RESULT.json for precise observations. Stop after this task; activation remains pending required managed restart.
