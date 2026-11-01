# One post-turn action — no live success yet

After this Codex result is **COMPLETED and published**, and no other task is running,
double-click:

`C:\Users\rustg\Desktop\Commands\Middleman\Finish Exact One.cmd`

This is an owner-launched foreground command, not a scheduled/detached auto-restart.
Do not run it from an active Codex task. If publication/idle checks fail it stops
without shutdown or installation. It never force-terminates a process, starts a
second tray, changes a bearer, POSTs another Inbox item, or releases historical HOLD.

When prompted, the only browser procedure is **Reload the existing Jarvis Inbox V1**
at `about:debugging#/runtime/this-firefox`, then refresh the NEW ChatGPT tab.
Do not load a second copy or click Send. The command waits for fresh no-send readiness
with exact binding/unique target/composer checks and the new exact-one content build.
No grant is armed while these are missing. If the add-on is absent, its existing
manifest is `C:\Users\rustg\Documents\Codex\Muse\bridge\inbox-v1\extension\manifest.json`.
No computer-use/browser automation or persistent add-on installation is used.

## What the command does

1. Verifies the prepared plan, pinned installer/lifecycle/pipe tool hashes, exact
   current turn identity and terminal publication in read-only SQLite, absence of
   other active/pending turns, original tray ownership and live idle health.
2. Uses the **existing** managed pipe's `shutdown-if-idle` (never force), bound to
   PID/start times and a unique channel hash. A race with a new turn is rejected
   by the bridge's own turn lock. Requires observed old-process exit.
3. Exclusively takes the existing `.runtime/instance.lock` byte before any source
   write. If a tray restart wins, installation stops. New bridge main cannot open
   queue/state while this lock is held. Imports may fail on a partial source bundle;
   existing hash checks fail closed and no grant exists.
4. Verifies the exact original14 #96 source hashes, reviewed17 staged hashes and
   unchanged queue/native journal/old hold. Fsyncs backups, then journal PREPARED /
   APPLYING. Replaces each source atomically, writes the derived full binding seal
   **last**, independently loads/verifies the new seal, then records COMPLETE.
   Recipient, generation1, epoch, HOLD, protected_history and every other binding
   field except components/identity are identical. No alias or hash bypass exists.
5. Releases the instance lock and waits for the **existing tray** to launch the
   coherent new bridge. Checks ownership, new PID, exact-one build and loaded
   component identity. If the tray does not recover, reports the exact idle tray
   Restart Bridge action; no process is killed or directly spawned.
6. Requests only no-send probes (bounded readiness polling, no Send retries).
   Stale receipts/old extension/old content cannot satisfy the new identity/build.
7. Only after readiness, exact unattempted item/hash, unchanged history and queue
   fingerprint checks pass, durably creates an exclusive owner arm-invocation audit
   and makes **ONE** existing authenticated exact-one arm call. Lost response or
   rerun never repeats this call. Concurrent owner commands are excluded by a local
   operation lock. Staged queue/browser one-use permits remain unchanged.
8. Monitors the exact existing test only. Reports terminal state/attempt count,
   grant state and historical digest/hold equality to local `attempt-result.json`.
   Never advances a cursor, retries a Send, rearms, or touches another entry.

The sole item is the already queued
`middleman-smoke-20261101-71c4fb280c:8715f59ac9710f1e355f50d284d3f2902d15a08470bdca4f7077a9a6fc004878`;
text SHA256 `1edebbb24c9c320d71a5c4d1369ccaa2e51c20e73d0a8ab157223b2679cac651`.
No second synthetic POST. Backend DELIVERED requires the staged exact new USER UUID/
payload proof; final senior nonce receipt is independent and is not inferred from tests.

## Prepared seals / local evidence

Old identity: `376671cc6cefba6f6e5f95284f13b7a96deb912518a3a0032ae97845bd3493c3`.
Derived next identity: `89d9cfb3df159b1c5e332d0be127fa37bdacad8f072d5dcf5bab4e740967921d`.
Generation1 / epoch `b2108916e5fb44098859a58e0252a2ad` / NEW recipient / HOLD persist.

Local-only audit/backups: `bridge/.runtime/inbox-seal-96/` (`plan.json`,
`activation.json`, `backup/`, later `journal.json`, `arm-invocation.json`,
`attempt-result.json`). No plan/backup/runtime store or credentials are committed.
Plan/journal seals detect alteration; activation pins the plan hash and source tools.
Existing secrets are not copied, printed, rotated or replaced.

## Rollback, never state rollback

If source installation raises an error, it attempts source/config rollback under
the same stopped-bridge lock. Power loss/interruption leaves an auditable partial
bundle, not a silently accepted seal. To restore before **any** grant/queue change,
from the Muse folder after the task is terminal:

```powershell
python -B dev/tools/inbox_exact_one/finish_once.py rollback
```

This also requires independent owner invocation, terminal task, idle shutdown if
the bridge is live, or the exclusive instance lock if imports prevented startup.
It verifies backups and known old/new file hashes; restores exact old source/config,
including removal of newly added files; verifies old seal and unchanged history.
If a grant/attempt/queue/journal changed, or the one arm invocation was recorded,
rollback **refuses**. It never rolls back a queue/claim/grant/audit, fabricates attempt0,
deletes an uncertain outcome, or downgrades a live exact-one queue to an old schema.
An interruption during rollback can be resumed by that same explicit rollback action.

## Narrow validation performed

#96's88 tests are reused, not rerun. New critical checks only:

```powershell
python -B -X utf8 dev/tools/inbox_exact_one/test_seal_migration.py
python -B -X utf8 dev/tools/inbox_exact_one/test_finish_guards.py
```

8 migration +3 launcher guard tests PASS: coherent same-recipient upgrade,
idempotence, changed source/stage/queue, missing exclusive ownership, plan tamper,
mid-install rollback, post-seal rollback, active-turn/uncertain-idle rejection,
exclusive concurrent arm-invocation and Codex ancestry rejection. No live Send.

Automatic approval review rejected a proposed in-turn `finish` invocation because
it can deploy/restart/arm. It did not execute; only inert `prepare` ran. No scheduler
or detached worker was armed. Production remains unchanged until the owner command.
