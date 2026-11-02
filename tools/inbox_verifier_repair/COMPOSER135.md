# Composer/USER identity policy and one seq135 receipt

This owner-authorized policy replaces rendered-Markdown equality as the delivery
gate. The submitted text is still checked byte-for-byte and SHA-256 in the
composer before the durable one-use permit and sole click. After that click,
exactly one fresh, visible, nonbaseline stable USER UUID must be observed on
consecutive samples, in the unchanged bound conversation, with the same empty
composer. Zero UUIDs, multiple cumulative new UUIDs, changed conversation/draft,
or uncertain Send remain NEEDS_REVIEW; there is no blind resend.

This is correlation evidence for the verified composer submission, **not** a
claim that the rendered body equals the original Markdown. It cannot attribute
content independently if an unrelated human message is the sole newly observed
turn while the submitted turn remains unobservable. The user explicitly selected
this practical policy; multiple observed turns are rejected rather than guessed.

Honest ACK/persistence fields:

```
verification_method = composer_hash_single_send_new_user_uuid_v1
composer_sha256 = verified pre-Send payload SHA-256
observed_sha256 = null
send_count = 1; new_user_turns = 1; composer_empty = true
user_turn_uuid = actual new stable USER UUID
```

Rendered text/hash/model observations remain bounded diagnostics. Their failures
cannot veto this proof. No raw React model availability is assumed. The future
ACK endpoint, native host and queue validator accept the named method only with
the documented composer/one-Send/UUID proof. Legacy exact-hash and explicitly
operator-attested records remain readable. Historical delivery remains HOLD.

New loaded proof/trace build: `inbox-composer-user-proof-20261102-01`.
Old loaded content cannot claim later results under the new bridge policy.
No model/route, permission, destination, lane ID, epoch, cutoff, queue format or
GitHub request behavior changes. Only source hashes/binding identity/lane seal
are coherently migrated; the actual ACTIVE lane/frontier is preserved.

## Deployment and seq135

`deploy_composer135.py arm` registers one demand-only pythonw Task Scheduler
instance. It waits for the exact authorizing Codex turn to be terminal, its
GitHub outbox published, and the bridge idle. It then uses the original tray's
managed graceful shutdown and existing instance lock. Source backups and the
existing atomic source-migration journal support rollback before receipt commit.
Rollback never restores or rewrites a queue.

Inside that exclusive window it installs the coherent source/binding/policy,
then applies ONLY `receipt135.py` under the real queue lock and fingerprint CAS.
That receipt uses original grant scope, exact retained trace, one original Send,
UUID and senior authority #45/6565939655. The failed automatic outcome is retained
verbatim and the receipt is labelled operator-attested. No permit, rearm, retry,
cursor mutation or receipt for136+ is created. If receipt fails, new code stays
fail-closed with135 held; it does not roll back a committed receipt.

The windowless task reports actual installed/receipt status directly to #45,
coordinates the exact new source identity/seal with Jarvis, waits for fresh new
loaded-build readiness and independently labelled Jarvis gate ACK, and monitors
136+ read-only. It stops on the first new review. Success requires136 and137
automatic composer/UUID ACKs plus Jarvis cursor>136/history proof. It self-disables
after one invocation. All child CLI calls use CREATE_NO_WINDOW.

Runtime audit/status: `bridge/.runtime/inbox-composer135-deployment/`.
Task: `MuseInbox-Composer135-Deploy-Once`. No recurring trigger or foreground
owner script is used. No browser GUI automation is attempted.

If Firefox has not loaded the installed build, the single browser action is:
**After #45 confirms installation, Reload Jarvis Inbox V1 in
`about:debugging#/runtime/this-firefox`, then refresh the bound ChatGPT tab.**
No manual Send. Native reconnect/readiness and the existing worker do the rest.
The one-shot waits up to one hour for loaded readiness, then stops with explicit
status rather than retrying a delivery. This document does not claim live success.

## Focused tests

- `node tools/inbox_verifier_repair/test_composer_proof.js`: 12 cases, including
  fences/UI controls, changed payload/composer, stale/wrong/zero/multiple UUIDs,
  missing Send permit, delayed rendering, idempotency and diagnostic failure.
- `python -B -m unittest discover -s tools/inbox_future -p test_future.py -q`:
  11 cases, including real native ACK path, honest null DOM hash, proof rejection,
  durable permit, oldest-first, restart ambiguity and historical HOLD.
- `python -B -m unittest discover -s tools/inbox_verifier_repair -p test_composer_deploy.py -q`:
  4 cases for rollback, stale loaded build, independent ACK and online-write refusal.
- Exact seq135 retained incident/UTF-8 authority/scope/fingerprint checked read-only.

27 focused cases passed. Earlier fixture failures were stale readiness fields and
Windows-decoded UTF-8 test text; corrected without weakening production guards.
