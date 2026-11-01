Double-click **Start Middleman.cmd** after a Windows restart. It reuses the existing
tray/bridge/App Server; **Check Middleman.cmd** is read-only. Keep the tray running.
No signed/persistent add-on installation is required or attempted.

After a Firefox/Windows restart, the one repeating browser procedure is:
Firefox `about:debugging#/runtime/this-firefox` > **Load Temporary Add-on** > select
`C:\Users\rustg\Documents\Codex\Muse\bridge\inbox-v1\extension\manifest.json`.
Refresh the intended conversation tab after loading (existing tabs need content injection).
Current authorized target: https://chatgpt.com/c/6ae5615a-0720-83ea-a43b-82386ce031e5
Keep exactly one matching tab open, with an empty composer and no generation active.

From the Muse workspace, request a no-send check (does not claim or ACK any delivery):
`python bridge/inbox-v1/binding.py request-readiness`
Start also requests this probe automatically; a later manual extension load can answer it.
Then run Check Middleman. A missing/expired receipt is NOT VERIFIED, not proof the
extension is absent. Receipt freshness is 60 seconds. Check never writes a probe.
Saved binding, loaded native/background/content readiness, and runtime validator build
are reported separately. NEW generation 1 on disk does not mean the browser loaded it.
Delivery remains **HOLD**, even when no-send readiness is READY. No historical item
is retargeted/replayed. End-to-end tests need separate authorization.

Validator activation: never restart an active turn. Once the current task has returned
and the monitor shows idle, use existing tray > Restart Bridge, then Check. The expected
loaded validator build is `inbox-recovery-binding-20261101-01`. No detached restart was
armed: the old activator is pinned to a different request/process and is not applicable.

For a future intentional thread change, inspect `python bridge/inbox-v1/binding.py status`,
then use the supported `binding.py rebind --target EXACT_URL --expected-id CURRENT_UUID
--expected-identity CURRENT_IDENTITY`. Supply the exact current values; stale values
fail closed. This creates a new epoch/generation while retaining HOLD and protected history.
Reload the existing extension, refresh the intended tab, request a fresh no-send probe.
Rollback uses `binding.py rollback` with the same expected-state arguments and the immediately
previous target; it creates a new epoch, never releases HOLD. Do not edit runtime JSON.

Exit codes: 0 READY, 1 DEGRADED, 2 BLOCKED. Whole-relay status stays DEGRADED pending
separately authorized end-to-end verification. `--no-pause` works for both CMD launchers.
Start logs retain 20 reports; Check writes no log. Neither submits tasks, sends messages,
ACKs queues, drains history, changes credentials/network policy, or restarts an active bridge.
Cold startup retains the existing pending-work safety checks. GitHub #45 is the coordination
channel; no manual Graham message relay is needed.
