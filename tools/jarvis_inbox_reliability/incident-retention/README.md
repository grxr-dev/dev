# Inbox V1 incident retention ? Windows deployment

FULL PASS. Native retention build `inbox-v1-incidents-20261011-01` is active. Extension verifier remains `inbox-v1-trace2-20261011-01`; no delivery criteria or browser code changed.

The confirmed design flaw was global four-file, 256 KiB rotation: subsequent delivery samples erased the held item's diagnostic records. Missing historical records cannot be reconstructed by this fix.

## Persistence and lookup

The native sink passes only its existing allowlisted, privacy-bounded record to the new best-effort sink, before independent rolling persistence. Each delivery stages its sanitized JSONL at:

`bridge/.runtime/inbox_verifier_incidents/active/<sha256(delivery_id)>.jsonl`

The first terminal NEEDS_REVIEW record (including native outcome on disconnect/restart) atomically moves the staging file to:

`bridge/.runtime/inbox_verifier_incidents/<sha256(delivery_id)>.jsonl`

Later terminal/native/ACK records append using fsync plus unique temporary file and atomic replace. Both exact delivery_id and derived request_id remain in every normal record. Find by hashing the exact delivery_id in UTF-8, or search retained JSONL request_id metadata. The extension's existing v2 candidate fields, baseline/send/deadline/conversation/binding evidence and bounded mismatch windows are preserved without reinterpreting them. Old rolling JSONL remains unchanged/readable.

A local-only deterministic fixture (no queue/API delivery) is available under `bridge/inbox-v1/test-evidence/retention-local/inbox_verifier_incidents/e2a3f3f2fab7edac27ed00af0a7357103c33a323346f78cb14d318d837ddf779.jsonl`, keyed by `local-retention-contract:` followed by 64 `d` characters.

## Exact bounds and cleanup

- Finalized incidents: at most 32 files /128 MiB combined, each at most16 MiB.
- Expiry: seven days since the last persisted record. Cleanup occurs on subsequent diagnostic writes; no new writes means no new growth.
- Capacity eviction: oldest files at least24 hours old first. Files under24 hours are protected. If all eligible capacity is exhausted, new diagnostics are dropped best-effort rather than evicting protected incidents or changing delivery decisions. This preserves several normal incidents comfortably; disk failure/cap saturation cannot guarantee new retention.
- Active staging: at most8 files of16 MiB; stale staging/overflow markers expire after24 hours. Successful/non-review ACK removes staging, creating no retained incident.
- Reserve64 KiB per staging file for terminal/ACK metadata. Above the sample budget, a bounded `incident_truncated` marker explicitly records incomplete evidence. No silent completeness claim at overflow.
- Atomic update scratch is at most one16 MiB file during a single native process update; stale scratch is cleaned after24 hours. Nominal live-data bound is256 MiB across active and finalized files, plus bounded scratch and the existing1 MiB rolling trace.
- Partial final staging lines after a crash are trimmed before subsequent append. Atomic replace failure preserves the previous finalized incident. Diagnostic failures are swallowed independently of ACK/outcome state.

No full payload fields, bearer, claim token or recovery-journal text are copied to incident files. Existing candidate/window caps are preserved.

## Validation

144 passing tests: content49, background10, old trace4, v2 analysis25, v2 trace8, hardening36, incident retention12. The stress regression writes6,000 later records (over2 MiB), rotates the original delivery out of all four rolling files, and requires its finalized incident to remain byte-identical. Coverage includes privacy, success cleanup, age/count/byte caps, protected young incidents, overflow marker, diagnostic I/O failure, native restart ambiguity, partial staging crash and failed atomic replace.

The unadapted hardening invocation could not bind the occupied production port18741. `run_hardening_isolated.py` runs the same36 tests on an ephemeral loopback listener and adjusts only disposable native fixture source/config; production local transport remains fixed at18741. The fixture now copies the new required module and checks its own journal, avoiding its old assertion about the real production journal. Windows temporary SQLite cleanup errors are ignored only in the isolated fixture.

Commands from Muse:

```powershell
node bridge/inbox-v1/tests/test_content.js
node bridge/inbox-v1/tests/test_background.js
python bridge/inbox-v1/tests/test_trace.py
python bridge/inbox-v1/tests/test_incident_retention.py
node dev/tools/jarvis_inbox_reliability/tracing-v2/test_candidate_analysis.js
python dev/tools/jarvis_inbox_reliability/tracing-v2/native-host/test_trace_v2.py
python dev/tools/jarvis_inbox_reliability/incident-retention/run_hardening_isolated.py
```

## Deployment and rollback

Installed native host patch/module and focused tests in the real bridge. Backup: `bridge/.runtime/inbox-retention-backup-20261011T091006Z/jarvis_inbox_host.py`.

Before reconnect: no DELIVERING items and null native recovery journal. Reconnected only the identified idle native Python process; Firefox's existing background reconnect started launcher283248/Python340100. Native readiness marker recorded at1791710092298ms. No extension code/reload, Firefox restart or bridge restart. Queue SHA256 was byte-identical before/after activation. No POST, synthetic smoke, resend, historical reconciliation, cursor operation or Linux/Brain Age change occurred.

Rollback: restore the backed-up host source and reconnect only when idle. The unused module can remain safely; preserve/export the incident directory. Rollback does not require deleting or changing queue/recovery/history files. No Graham action remains; the next natural NEEDS_REVIEW will finalize its own incident.
