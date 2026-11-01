# FUTURE_ONLY new-result lane — not live / end-to-end not proven

This reuses the deployed Inbox engine, native/background/content verifier, durable
one-use Send permit and managed owner lifecycle. It does not release binding HOLD,
alter the finished #95 grant, or replace the relay. Brain Age remains paused.

## Exact next action after this task publishes and the bridge is idle

Double-click `C:\Users\rustg\Desktop\Commands\Middleman\Finish Future Delivery.cmd`.
The foreground command independently verifies the exact terminal/published task,
idle health, original tray, pinned sources and legacy hashes. It uses the existing
managed `shutdown-if-idle`, proves exit and holds the existing instance lock while
the tested journaled source/seal upgrade runs. No force kill, detached scheduler,
new bearer or direct private-process launch. It preserves every binding field except
reviewed components/identity. Current seal is `89d9cfb3df159b1c5e332d0be127fa37bdacad8f072d5dcf5bab4e740967921d`;
next source seal is in `source-manifest.json`. Recipient/gen1/epoch/HOLD do not change.

The installed mode is **PREPARED / DISABLED** per senior #45 comment6560156429.
Reload the existing Firefox Jarvis Inbox add-on once and refresh the NEW tab when
prompted. No Send. Native polling automatically refreshes future readiness; there
is no per-message script. Old extension/content cannot satisfy the future-build and
lane-seal receipt. The command publishes actual loaded PREPARED readiness and legacy
hash proof directly to #45. It does NOT turn that readiness into live authority.

Temporary manifest, if absent: `C:\Users\rustg\Documents\Codex\Muse\bridge\inbox-v1\extension\manifest.json`.
No browser automation, permanent extension/signing, synthetic or #95 resend.

## After separate positive senior live authorization

Senior can post a RAW JSON comment on #45 (no Markdown fence) matching the installed
PREPARED readback:

```json
{"action":"ACTIVATE_FUTURE_ONLY","prepared_seal":"EXACT_PREPARED_LANE_SEAL","binding_identity":"EXACT_LOADED_BINDING_IDENTITY","conversation_id":"6ae5615a-0720-83ea-a43b-82386ce031e5","historical_policy":"HOLD"}
```

Only an explicit local owner invocation can consume it; there is no public/remote
activation endpoint or inference from caller flags/request prefixes. The owner uses:

```powershell
python -B dev/tools/inbox_future/finish_future.py activate --expected-seal EXACT_PREPARED_LANE_SEAL --authorization-comment EXACT_POSITIVE_COMMENT_ID
```

It reads that exact authenticated GitHub control-channel comment/account/scope,
checks fresh unique NEW binding/readiness and records authorization locally. It
requires the unused PREPARED lane. Under a SQLite writer reservation it snapshots
both production high-water marks and atomically publishes ACTIVE before releasing
producers. Thus records created between installation and live activation are also
excluded. A new lane ID/seal is minted; it cannot reuse PREPARED cutoffs. This needs
no bridge restart. New native/background/content lane-seal readiness is required
again before a claim. Owner readback is posted directly to #45; no message copying.

Jarvis's separately authorized activation record and future worker must match this
ACTIVE checkpoint on every run. Its legacy cursor93/43-record store and cursor57
remain untouched. Its disabled worker/new state is independent, not a legacy skip.
Do not wire/enable it before senior approval and matching active metadata. Only
after that is the single NEW cheap synthetic result requested. No such task or
Inbox POST has been created here. No live/automatic-delivery PASS is claimed.

## Eligibility and invariants

* Producer-controlled `completions.sequence > completion_cutoff` AND persistent
  `requests.rowid > request_cutoff` (github/http source). Existing producer code
  retains request IDs and never deletes/reuses them; it is included in the seal.
* Exact local stored request ID, server event identity, response and SHA256 must
  match `<request_id>:<response_sha256>` and `[CODEX → CHATGPT]\n\n<verbatim response>`.
  A late old result, new caller timestamp/flag/prefix, unknown ID or rewritten text
  never grants eligibility. Old pending requests finishing later are excluded too.
* Existing legacy IDs return existing evidence only; ineligible unknown posts are
  rejected. No write to `inbox_queue.json`, old grant/recovery, HOLD or VM cursors.
  Both legacy file hashes are checked for every future operation.
* The new `inbox_future_queue.json` uses the existing InboxQueue format/atomic engine.
  Future grant/source/Send-intent metadata is durable inside its own entries only.
  No second service, broad RPC or browser control API exists.
* Trusted source sequence ordering governs claims, not POST order. Missing earlier
  eligible results or an ambiguous/permanent terminal result block later ones.
  A retention gap blocks; it is never silently skipped. Delivered metadata retains
  the known frontier so ordinary retention after delivered results is safe.
* One claim/attempt and one durable permit per item. A lost reply, restart or timeout
  never forwards it again. Known matching ACKs are idempotent. DELIVERED still
  requires exact payload hash, a new stable USER UUID, one Send and empty composer.
* PREPARED exposes readback but no eligible events, enqueue or claim. ACTIVE metadata
  is authenticated on existing events GET: `future_lane`, `future_eligible`,
  `future_result_sha256`, `future_request_ordinal`. No new remote caller authority.

## Focused checks / deployment audit

17 Windows checks passed, not a broad suite:

```powershell
python -B -X utf8 dev/tools/inbox_future/test_future.py
node dev/tools/inbox_future/test_future.js
python -B -X utf8 dev/tools/inbox_future/test_upgrade.py
```

10 provenance/ordering/native/disabled/activation-boundary checks;5 shared browser
grant checks;2 actual-source migration/rollback and activation-scope checks. Existing
#96/#97 verifier/lifecycle logic was reused. These are not live browser evidence.
Jarvis reports21 disabled VM fixture checks passing (#45 comment6560241301); those
were not executed on Windows. Its pagination edge is being confirmed directly.

Runtime audit/backups only: `bridge/.runtime/inbox-future-deploy/`. No runtime store,
credentials, browser data, private results or backups are committed. Source overlay
is in `production/`; it is not installed by a blind copy. `source-manifest.json`
pins the actual predecessor and reviewed new bytes. Source plan and installer/tool
hashes are pinned; new binding is derived, never aliased or bypassed.

Before any ACTIVE state or future-store creation, rollback is:
`python -B dev/tools/inbox_future/finish_future.py rollback` from the Muse folder.
It uses the same idle managed shutdown/instance lock, verifies the exact owned
PREPARED policy and unchanged history, removes only that unused policy and restores
source/config from the journaled backups. Once ACTIVE or the future queue exists,
source rollback refuses; it never restores old queue/grant/claim/cursor state.
An install exception restores source/config while still holding the instance lock.
If the old tray doesn't recover, use its existing Restart Bridge only while idle;
the installer never kills or directly replaces the tray/credentials.
