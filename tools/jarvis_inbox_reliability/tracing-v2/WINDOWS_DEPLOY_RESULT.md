# Windows Tracing v2 deployment ? PARTIAL

Installed and tested; Firefox activation awaits Reload. [Result JSON](WINDOWS_DEPLOY_RESULT.json) records exact before/after hashes, backup path and evidence. [Installed integration diff](windows-installed.patch) records all changes to existing production files; candidate_analysis.js is copied byte-for-byte from the committed source.

Source commit `babd3357c1e490fac7d045e4742fb0629a8980e6`. All six original package files match committed Git blobs (Windows checkout line-ending filters applied). Repository fast-forward changed only the infrastructure package; Brain Age Task AM files/runtime were untouched, Task AN not started.

Both supplied patches are syntactically malformed (`corrupt patch`, content line16/native line37); content also includes a placeholder instead of actual baseline context. Exact tracing-v1 production anchors were validated before intentional integration. Shared candidate_analysis.js is loaded first via the manifest, with no duplicate inline implementation. Original canonicalization, UUID snapshots, payload/hash gates, stable two-sample match, idempotency, ambiguity/no-resend and Send site remain unchanged. New analysis/hash/helper failures are isolated and swallowed so tracing cannot change delivery outcomes. Observational conversation parsing supports the existing project conversation URL form and records identity on terminal unbind as well as samples. Branch indicators remain conservative heuristic evidence; absence is unknown, not proof of a linear thread.

The package documented extension/ and native-host/ subdirectories but actually committed the two JS files at its root and omitted test_trace_v2.py. The committed root JS tests were run, and eight Windows native-schema tests were added under native-host/test_trace_v2.py against the installed production host. Existing content harness loads the shared helper, with four extra failure-isolation/integration tests.

All **126 tests passed**: content49, background10, existing trace4, committed candidate analysis25, added native v2 schema8, isolated native/queue30. No test failures or fixture errors occurred in this deployment. Logs are under bridge/inbox-v1/test-evidence/trace2-*.log. New schema accepts bounded mismatch fields and rejects unknown/full-payload fields; v1 compatibility and trace rotation remain tested. Real existing trace JSONL/rotations are still parseable. No real production trace event or synthetic message was injected.

Production files changed:
- inbox-v1/extension/chatgpt_content.js
- inbox-v1/extension/candidate_analysis.js (added exact shared source)
- inbox-v1/extension/manifest.json
- inbox-v1/native-host/jarvis_inbox_host.py
- inbox-v1/tests/test_content.js

Backup: `bridge/.runtime/inbox-trace2-backup-20261011T082319Z`, with original file hashes and relative paths. Installed build is `inbox-v1-trace2-20261011-01`; **active Firefox build is unverified**. Native schema is verified through isolated production-code tests, not an active respawn claim.

Before reload attempts, queue DELIVERING count was0 and native recovery journal null. Computer-use node_repl failed Windows sandbox initialization (`helper_unknown_error: setup refresh had errors`); alternate browser-control kernel exited unexpectedly. No extension reload/native reconnect was performed. No bridge/Firefox restart was attempted or required. No queue/cursor/history record was mutated, reconciled, skipped or resent by this task.

Remaining manual step: while no delivery is in flight, Firefox **about:debugging -> This Firefox -> Jarvis Inbox V1 -> Reload**. Reload reconnects native messaging and loads the updated host. No synthetic smoke: leave the system for the next natural result, potentially this deployment task's completion. Its trace should show the v2 build and new mismatch/conversation fields. Before that reload, already-loaded tracing-v1 can continue operating; activation is not complete.

Rollback while idle: restore the four backed-up original files, then reload the extension; the added helper can remain unreferenced. Preserve queue/journal and existing trace history. No Brain Age follow-up is authorized or started.
