# Relay reliability gate (Windows staged / Jarvis acceptance pending)

See `../../docs/Relay_Continuity_Hardening.md` and `contract.json` before activation. **Brain Age is intentionally paused after AW16. This tooling never creates an inference or successor.**

`runtime/` is reviewed ROM-free Windows infrastructure source, not live state. `runtime-manifest.json` binds exact file bytes. The installed bridge currently owns the active hardening turn and cannot safely restart itself. `stage.py` only stages source after an explicit reviewed baseline fingerprint; staging is not activation.

From the Muse workspace root:

```powershell
python -X utf8 dev/tools/relay_reliability/test_continuity.py
python -X utf8 dev/tools/relay_reliability/stage.py --bridge bridge
python -X utf8 dev/tools/relay_reliability/check_activation.py --bridge bridge
```

The activation check returns nonzero for old loaded code; this is intentional. After a separate idle managed activation, require owned PID/start identity, exact module hashes, listener/route manifest and admin capability before any administrator operation. Never force-stop the current task.

Optional explicitly installed read-only observer (private state must stay ignored):

```powershell
python -X utf8 dev/tools/relay_reliability/watch.py --bridge-source bridge --store dev/local/relay-reliability/observer.sqlite3 --once
```

Discovery always backfills GitHub open/closed issues; local high-water never suppresses older unseen comments. Historical conflicts are preserved in a per-issue quarantine with exact evidence/hash. The observer cannot deliver to a browser, dispatch a task, clear a project pause or create a successor. It is not automatically installed as Jarvis's deployed result_poller.

Reuse existing synthetic issue #87 / result6215141578 and direct #45 signal6215143552 for cross-side acceptance. Do not blindly create another smoke or repeat an uncertain POST. The original smoke script reconciles durable POSTING state by exact readback, never blind resend. Production workers were not disabled/restored by the test; its HTTP404 endpoint and Inbox outage are explicitly injected.

The 14 required faults and outstanding live/VM checks are listed in the report and contract. Python's standard library and the existing `gh` credential store are used. No credentials, SQLite, prompts/results, queues, runtime tokens or private captures belong in Git.
