# Inbox V1 reliability repair - PARTIAL

The on-disk production verifier is patched and focused tests pass. Strict completion ordering and live permanent-thread validation remain blocked. This is not a completed production deployment.

## Findings and minimal change

The old verifier sampled only viewport-visible turns, required exactly one newly visible turn, terminated immediately on partial text or multiple new turns, and timed out after 30 seconds. Those code paths can label a posted message ambiguous during rendering, virtualization, or DOM replacement. The specific DOM cause for AA/AB/AC could not be inspected, so it is not established as one particular selector defect.

The new verifier snapshots all existing user identities independently of text parsing before Send. After its sole Send it samples connected historical user turns for up to 90 seconds, within the existing background 120-second timeout. Positive proof requires a non-baseline message identity with exact canonical payload text and SHA-256, stable across consecutive samples. Partial/mismatched or unrelated turns do not terminate verification early. Multiple exact new identities remain ambiguous. The canonical transformation, visible payload, deterministic delivery IDs, pre-Send draft protection, native ACK schema and bearer separation remain unchanged. Unverifiable sends stay NEEDS_REVIEW and cached outcomes never cause another Send.

The completion-order violation cannot be traced or fixed from available local code: `goals/brain-age-codex-result-watcher/hidden_files/inbox_deliver.py` is absent from Muse and the Windows user directory. The queue chooses the oldest eligible item and can skip NEEDS_REVIEW items, but it has no completion sequence/cursor knowledge. Changing that generic queue would not prove the required watcher invariant. No substitute watcher, speculative cursor changes, historical replay or new IDs were introduced. Actual watcher host/path/access is required to inspect the durable cursor and serialize its oldest unresolved completion across invocations. No claim is made that ordering is repaired.

## Changed files and evidence

Only these production files changed:

- `bridge/inbox-v1/extension/chatgpt_content.js`
- `bridge/inbox-v1/tests/test_content.js`
- `bridge/inbox-v1/tests/test_background.js`

Existing synthetic tests retained a retired conversation ID; they now test the unchanged production binding `6acab580-d218-83ea-9598-0ff64dc33aa7`. New tests cover delayed rendering beyond the old deadline, partial text, unrelated new turns, hidden/unparseable baseline identities, offscreen exact turns, transient identity changes, and duplicate exact matches. Existing no-resend/hash/draft/idempotency tests remain.

Backups: `C:\Users\rustg\Documents\Codex\Muse\bridge\.runtime\inbox-reliability-backup-20261011T003730Z`

Local evidence: `bridge/inbox-v1/test-evidence/reliability-tests.json`. The committed `verification.patch` captures exact production-source/test changes for this otherwise unversioned bridge; `RESULT.json` records limits and tests. No Brain Age source, outbound implementation, Relay V2 configuration, native host, bridge route, queue or cursor changed.

## Tests

- Content verifier/DOM contracts: 26/26 passed.
- Native reconnect/background contracts: 8/8 passed.
- Isolated queue/native hardening: 30/30 passed, including idempotency, hash proof, genuine ambiguity, concurrent queue access and ACK recovery.
- GitHub outbound-only regression: 2/2 passed.
- Watcher oldest-first/concurrent invocation: NOT RUN, helper unavailable.
- Live smoke / duplicate POST: NOT RUN, no delivery ID or token created.

An initial full hardening invocation could not run its HTTP handler class because the real native listener already owns 18741. The queue/native classes were then run separately without interrupting production. This is not a full HTTP-suite pass.

Reproduce content/background and outbound checks from Muse:

```powershell
node bridge/inbox-v1/tests/test_content.js
node bridge/inbox-v1/tests/test_background.js
python -X utf8 -m unittest discover -s bridge -p test_github_outbound_only.py -q
```

For queue/native classes, load `bridge/inbox-v1/tests/test_hardening.py` with importlib and run only QueueTests and NativeTests. Do not stop the production listener just to run HandlerTests.

## Deployment blocker and next bounded steps

Both Windows computer-use and browser initialization failed with `windows sandbox failed: helper_unknown_error: setup refresh had errors`. The current DOM could not be inspected and the temporary extension could not be reloaded. The edited file on disk does not prove Firefox is running it. No smoke was posted through old/unverified code, and no manual ChatGPT send substituted for production delivery.

To finish: provide the actual production watcher helper/host access; fix its oldest-first cursor transaction and interprocess lock, test unresolved N blocking N+1 and concurrent invocations; restore browser access or reload Inbox V1 through Firefox about:debugging and reload the bound ChatGPT tab when its composer is empty. Then perform exactly one authorized unique smoke through authenticated POST /chatgpt-inbox and verify DELIVERED plus duplicate suppression. Keep the permanent binding unchanged. Do not replay historical completions.

No bridge restart is needed for this JavaScript-only patch. Production extension reload is required. Normal relay completion reporting is left to the existing bridge; no direct result-delivery bypass was used.
