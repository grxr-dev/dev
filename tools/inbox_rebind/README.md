# Middleman held recipient binding — local non-browser completion

PASS for the bounded local source/tests/launcher work only. No Inbox delivery or
end-to-end test was performed. Production policy remains HOLD. Brain Age unchanged.

This preserves the issue #92/#93 implementation rather than replacing the relay.
`production/` is an overlay of eligible source files for the existing Muse bridge,
not a second bridge. `middleman/` contains the installed Desktop launcher/runbook.
`source-manifest.json` hashes exact deployed source bytes (raw line endings retained).
No runtime config, queue, credentials, backups, browser data or payloads are bundled.
Do not blindly overwrite a different production version or edit a running queue.

The persistent binding is NEW `6ae5615a-0720-83ea-a43b-82386ce031e5`, generation 1,
epoch `b2108916e5fb44098859a58e0252a2ad`, with HOLD and historical hashes protected.
Component hashes bind coherent native/extension/validator source. Native config is
the only recipient source; background and content must echo the same identity.
Both historical delivery claims and ACK replay fail closed while HOLD is installed.
The old test-only `bind_disposable.py` editor is retired. Future deliberate changes
use the compare-and-set `binding.py rebind/rollback` controls; neither grants Send.

The continuation fixed recovery readiness's too-small request bound (128 to 256
bytes), checks content identity, blocks recovery hold release, and gives the validator
the distinct runtime marker `inbox-recovery-binding-20261101-01`. Generation/epoch/
recipient/HOLD did not change. Local backups are outside version control under
`dev/local/inbox-rebind/` (baseline, continuation and final-local).

## Live evidence and remaining activation

Bridge PID 27972, tray 37780, App Server 20652 remained the same across Check and two
Start invocations. Health, monitor and local Inbox capabilities were healthy. Start
reuses these processes and requests only a held no-send readiness probe; Check is
read-only. Neither invokes next/ACK/recovery, changes credentials, or sends messages.

A real native receipt at `1793516136232` ms reported native PID 22188, exactly one
NEW tab, content reachable/bound, composer present/empty, no generation or delivery
active, and matching current binding identity. It is real no-send evidence obtained
without browser control. Receipts expire after 60 seconds; no receipt means NOT
VERIFIED, not necessarily absent. `RESULT.json` is a sanitized observation report,
not an authoritative runtime store.

**Validator is STILL NEEDS POST-TURN ACTIVATION.** Existing authenticated local GET
reports `inbox-recovery-once-20261015-01`, independently of the new disk source.
No restart was performed/armed during this active bridge-owned turn. The old detached
activator is request/PID-pinned and would perform unrelated recovery; it is unsuitable.

Exact supported action after this task returns and the monitor is idle: existing tray
menu **Restart Bridge**, then **Check Middleman.cmd**. The existing tray performs a
live `shutdown` with `if_idle=true`, requires accepted acknowledgement, and retains
the same in-memory bearer across bridge restarts. Do not exit/restart the tray itself.
Expected validator status afterward: LIVE / `inbox-recovery-binding-20261101-01`.
This action was inspected, not invoked; no activation success is claimed.

Jarvis authenticated VM events GET was last verified by #45 comment 6554363878.
This task did not retrieve/reprovision its secret or claim a new VM-side test. The
completion report on #45 asks Jarvis for only an authenticated read-only events GET.

## Exact manual browser procedure (only after absence/restart)

Firefox `about:debugging#/runtime/this-firefox` > Load Temporary Add-on > select:

`C:\Users\rustg\Documents\Codex\Muse\bridge\inbox-v1\extension\manifest.json`

Refresh the intended NEW tab after loading. Keep one matching tab, an empty composer
and no generation. No signed add-on, publication or browser automation is involved.
At the observed fresh READY receipt, no browser action was required.

Installed Start/Check: `C:\Users\rustg\Desktop\Commands\Middleman\`.
From Muse, optional explicit checks:

```powershell
python bridge/inbox-v1/binding.py status
python bridge/inbox-v1/binding.py request-readiness
python bridge/inbox-v1/middleman_status.py
```

## Validation

```powershell
python -X utf8 dev/tools/inbox_rebind/test_binding.py
node dev/tools/inbox_rebind/test_binding.js bridge
python -X utf8 dev/tools/inbox_rebind/test_status.py
python -X utf8 dev/tools/inbox_rebind/run_regressions.py
```

70 authoritative tests passed: 18 Python binding, 10 JS binding/background/content,
5 status, and 37 selected existing queue/idempotency/native-wire/trace/retention
tests including 6000-event rolling-rotation stress. PowerShell parser passed.
Binding tests include persistent fresh-process readback, idempotence, stale epoch/
recipient rejection, atomic failure, rollback, hidden-tab rejection, HOLD/no HTTP/
ACK paths and recovery release denial. Two Starts reused all three existing PIDs.

Legacy full runs were also attempted and are **not all green**: trace 2/4 failed;
retention 2/12 failed; hardening 5/30 native cases failed/errored plus HandlerTests
setup failed because production owns its hard-coded 18741 port. Those fixtures assume
an unconfigured native host may deliver/ACK. The new mandatory binding/HOLD correctly
rejects that assumption. No product gates were loosened, no production port freed,
and those test sources were not rewritten to conceal failures. The explicit regression
selector documents exclusions; the new binding tests cover the new native contract.

Queue, pending native outcome journal and old readiness hold were SHA-256 identical
before/after. No cursor, seq94/backlog, history, ACK or reconciliation was changed.
No send/synthetic/end-to-end claim; separate authorization and verification remain
required. No Brain Age continuation.

Rollback: preserve held runtime/history; restore the coherent backed-up source and
matching binding config only while idle under owner control, never remove HOLD or
retarget history. Do not use the obsolete test recipient editor. Keep old backups.
