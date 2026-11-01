# Inbox rendered-text false negatives: raw user-message proof

## #110 supersedes the owner instructions below

The #108 bundle is now **installed and loaded** with the reviewed identity
eb789679… and seal975fe745…. The failed maintenance gate required an old DOM
node to be rendered. That gate is removed from the maintenance helper only;
production verifier/seals/ACTIVE lane/cutoffs are unchanged. Historical seq133
uses the pinned trace + senior operator receipt, never a new Send or invented
automatic DOM proof. A fresh no-send current-content readiness probe passed.
It proves loaded capability/binding/composer readiness, not raw-model extraction
on a currently rendered message. The latter must be proved by normal new delivery.

**No user scroll, Reload or foreground script is required.** One demand-only
Task Scheduler invocation `MuseInbox-Seq133-Receipt-110` is armed through the
existing interactive-owner mechanism. Independent ancestry and exact scheduled
action were verified; it is waiting for the pinned #110 task to be COMPLETED,
GitHub outbox CLOSED, and the bridge unambiguously idle. It checks source hashes,
PID/start identity, original tray, VM alignment ACK and fresh no-send readiness
before the existing managed shutdown-if-idle and instance lock. It never kills
an active turn, reinstalls source, releases historical HOLD or creates a Send
permit. It uses the queue's lock/atomic receipt writer once and self-disables.

The worker rejects generic Jarvis auto-ACKs: the control-channel reply must attest
the exact identity/seal, same cutoffs and cursor132, tied to request6564661930.
Its single receipt commit lets the existing VM worker progress naturally. On a
new NEEDS_REVIEW, monitoring stops and retains that specific incident without
further reconciliation or resend. Success still requires cursor>135,134/135 once,
one new automatic raw-model proof, and unchanged historical hashes.

Runtime-only execution evidence is under
`bridge/.runtime/inbox-seq133-postturn-110/` (`state.json`, registration, console,
receipt-result). Original migration evidence remains intact. Eight narrowly
focused #110 tests passed; the prior32-test suite was not repeated. The task has
no trigger/recurrence and cannot be rearmed by the helper. `postturn_receipt.py`
refuses an existing plan or an already-used invocation. No new Codex task is made.

Everything below describes the earlier #108 owner-run phase, not a request to run
it again.

Status: **prepared, not installed/live**. No production queue, cursor, historical
HOLD, source, binding, lane or process was changed by the Codex turn. No seq133
Send/rearm/reconciliation occurred. Do not call this a live fix until the owner
command's `live-validation.json` says `LIVE_AUTOMATIC_DELIVERY_PROVEN`.

## Exact remaining owner action

After the task's terminal result is published, run:

```powershell
& 'C:\Users\rustg\Documents\Codex\Muse\dev\tools\inbox_verifier_repair\Finish Relay Repair.cmd'
```

When the command prompts, perform the one unavoidable browser step:
**Firefox `about:debugging#/runtime/this-firefox` → Reload the existing Jarvis
Inbox V1 extension, then refresh the NEW ChatGPT tab.** Do not Send anything.
The old loaded background has no supported native-command reload capability.
This task does not use GUI automation, browser policy workarounds, signing,
additional permissions or a new relay. No user message relay is needed.

The launcher does all coordination directly on #45. It rejects Codex ancestry,
waits for the pinned task's terminal/outbox publication and no active/pending
request, then uses the original tray's `shutdown-if-idle` and original instance
lock. No force kill, parallel bridge, scheduler job or detached restart is used.
It installs the five changed component files plus coherently derived binding and
policy seals in the verified stopped ownership window. Recipient/gen/epoch/HOLD,
ACTIVE lane ID, cutoffs129/129 and all future/historical entries remain unchanged.
Original terminal grants are not rewritten or reissued.

Before changing seq133, while it exclusively owns the stopped bridge, it requires:

1. Loaded native/background/content readiness: exactly one correct tab, bound,
   composer present and empty, no generation/delivery, correct new source identity
   and lane seal, proof build `inbox-raw-user-proof-20261101-01`.
2. A **no-send** lookup of seq133 UUID41bfef82-0c00-4014-9f22-11adbf4345f5 yielding
   a user-authored text model whose exact SHA is the queued payload SHA0fa4ef79….
   If the framework model is unavailable, conflicting or wrong, stop. No guess.
3. Jarvis's exact structured ACK of the coordinated VM activation-record
   identity/seal change, retaining cursor132 and the same lane/cutoffs/history.
4. Fresh no-send proof again, pinned future queue fingerprint, trusted completion,
   retained incident hash and exact operator authority #45/6561830626.

Only then it uses the reviewed InboxQueue receipt kernel to commit seq133 as
**operator-attested**, preserving its original failed automated outcome, grant,
claim token, attempt1 and Send intent. No new Send permit or fabricated DOM ACK.
The original tray resumes normal ownership after maintenance exits. The existing
VM worker alone advances its cursor and delivers134/135 in order.

The launcher then reads Windows state/trace plus Jarvis's read-only proof. Full
proof requires both134/135 delivered automatically once, cursor>135, one new
delivery with two exact raw-model hash samples and one Send event, unchanged
historical hashes and no later NEEDS_REVIEW. It never posts a synthetic result,
forces ACK, advances a cursor, or automatically retries a maintenance failure.

## Verification change

`body.innerText` represents rendering, not original message bytes. The new primary
source is the authorized content script's read-only view of the UUID-matched
React message model: `id`, `author.role=user`, `content.content_type=text`, string
`parts`, and conversation identity when present. Firefox's `wrappedJSObject`
exposes framework data without eval, page-function calls or new permissions.
Traversal uses own data properties on message/container paths with strict bounds.

It verifies exact raw-model text/hash against the exact pre-Send composer payload,
the original single durable Send intent, a non-baseline stable USER UUID on two
samples, unchanged bound conversation, and empty composer. A wrong/conflicting
model cannot fall back to a convenient rendered match. Existing exact rendered
fallback remains for model-unavailable legacy turns; it is not a fuzzy path.
Nothing strips arbitrary suffixes or changes sent payloads/normalization.

The no-send diagnostic uses the existing readiness/native channel. It persists
only model/rendered hashes and lengths, stable UUID and capped tag/text-length
structure; no chat body, attributes/URLs or authentication material. Its pending
request survives native automatic freshness probing once, then routine freshness
probes resume. It does not call insert, deliver, Send or claim.

## Evidence and limits

Seq132 retained trace: normalized991 vs extracted1003, mismatch991 END/newline.
Seq133: expected1287 vs extracted1285, mismatch89 backtick/0; triple backticks
disable the old inline normalization. Simple delimiter/suffix transformations did
not reproduce its observed hash. These are distinct shapes. The actual trailing
node and complete rendered transformations remain **unproven**, not invented.

`rendering-shapes.html` and model tests are explicitly synthetic/redacted, not a
live DOM capture. The installed-channel no-send activation probe must establish
real raw-model availability and save privacy-minimized live provenance to
`bridge/.runtime/inbox-verifier-repair/provenance-readback.json`. Firefox GUI
inspection is not attempted. No public report includes private result bodies.

## Focused tests

```powershell
node dev/tools/inbox_verifier_repair/test_model.js
node dev/tools/inbox_verifier_repair/test_probe.js
python -B dev/tools/inbox_verifier_repair/test_migration.py -v
python -B dev/tools/inbox_receipt_132/test_receipt.py -v
```

32 focused tests pass:12 model/DOM,2 background,9 migration/native/privacy,
9 reused atomic-receipt regressions. They cover Markdown/codefence/newline/autolink
render variations, altered payload, wrong author/conversation, old/conflicting
UUID, getter safety, diagnostic privacy, stale loaded capability, owner-probe
handoff, seal continuity, rollback injection, replay/concurrency and no Send grant.
No broad suite or production delivery was run.

## Audit and rollback

Runtime-only plan/backups/incident/activation/proof/result are under
`bridge/.runtime/inbox-verifier-repair/`. No credentials or runtime stores are
committed. The existing source installer journals per-file atomic changes and
commits binding last; policy seal follows under the same exclusive ownership.
Exceptions restore the old policy and original source bytes without queue edits.
An interrupted bundle remains fail-closed. Before receipt commit only, the explicit
owner rollback is:

```powershell
python -B dev/tools/inbox_verifier_repair/finish_repair.py rollback
```

Rollback uses the same idle/instance guards, refuses changed queues and committed
receipts, and coordinates the old VM source gate on #45. Browser Reload may be
needed to match restored source. **Never restore a before-queue after a committed
receipt**, because the VM may already have progressed. Post-commit uncertainty is
read-only diagnosis, never another reconciliation or Send.
