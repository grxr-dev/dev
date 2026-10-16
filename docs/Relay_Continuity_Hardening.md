# Relay continuity hardening (#85, clean resume #88)

## Decision

**PARTIAL. Reliability gate safe to clear for AW17+: NO.** Windows source is implemented/staged and tested; a GitHub-authoritative reference consumer and real GitHub smoke are proven. This is not a claim that Jarvis's deployed poller/planner has been replaced or certified. The active bridge still runs its older build. No Brain Age source, evidence, gameplay state, successor, model routing, credentials, conversation binding, network policy, or approval policy changed.

## Recovery of #85

#85 left uncommitted `tools/relay_reliability/`, the matching staged Windows sources, 26 focused tests, 67 relay/completion regressions, 26 supersession tests, 31 recovery tests, and the tray policy suite. It had already published synthetic issues #86/#87 and direct #45 signals. All were retained. No additional synthetic issue/result was created on this clean resume.

#86 is historical test evidence, not final acceptance: the PowerShell patch pipeline replaced a Unicode envelope arrow with `?`, and initial API propagation was delayed. #85 corrected the source to explicit Unicode escapes, added production-generated multipart interoperability, and obtained the clean #87 smoke. Original failed evidence remains local. No posted message or authoritative record was edited to manufacture a pass.

#85's full backfill failed closed before commit. The concrete cause is issue #9 versus #72: both use `brainage-task-y-001`, but their exact envelope hashes differ (`a6d385ec24c9ab5022712569483ee425475dcce8ea642ec4ad9e9295b05d11a6` versus `a96a51c771e9a6603a08feb3fe6fc27b8d3bc9b28f6a4891f8981353c2840766`). This resume adds per-issue savepoints inside an explicit outer transaction and immutable quarantine evidence. The conflict is not accepted/overwritten; unrelated discovery continues. An actual rollback test caught SQLite RELEASE committing an outermost savepoint; explicit `BEGIN IMMEDIATE` fixes it. The successful resumed read-only backfill ingested **82 results**, retained the issue #72 conflict, and recorded AW16 intentional pause. No existing live cursor/database was reset.

## Actual architecture audit and failure modes

| Component / actual path | Dependency / symptom | Detection and recovery before hardening | Can stall? | Hardening / remaining work |
|---|---|---|---|---|
| Jarvis result_poller, VM only | Windows numbering unavailable; negative issue fallback compared below positive cursor | Jarvis #45 reports provisional-above-highest patch; exact deployed VM source unavailable here | Yes historically | Canonical GitHub receipt/request/result identity; local immutable AUTOINCREMENT; bridge sequence enrichment only. VM integration/activation evidence required |
| Reference GitHub reader `continuity.py:Poller` | Duplicate/edited request or terminal comment | Original all-or-nothing batch rejected all on historical conflict | Explicit failure, but starved valid backfill | Per-issue quarantine with exact evidence/hash; valid receipts/results and health commit together; no silent skip |
| Reference durable store | Crash, partial file, restart, out-of-order result | No deployed replacement previously | Yes | SQLite WAL/FULL, integrity check, atomic poll transaction, exact receipts, bounded full open/closed backfill, cursor never filters existence |
| Jarvis watchdog / successor planner, VM only | Inbox/sequence cursor or stale nudge confused with project state | #45 human-independent direct channel exists; pause ACKed | Yes historically | Durable unique senior-review intent; pause-before-stall logic. Reference never launches tasks. Jarvis must bind its actual successor reservation/reconciliation to contract |
| Windows `github_bus.py`, `relay_state.py`, `completions.py` | GitHub/API or uncertain comment POST | SQLite outbox + exact readback; POSTING/UNCERTAIN never blindly re-POSTed | GitHub publication can degrade | Preserve existing semantics; add durable worker status/backlog/backoff and usage request retention; paused Brain Age entries cannot starve unrelated intake |
| Windows `bridge.py:Handler.do_GET` | Wrong `/completions` path; stale route registration | `/health` existed, exact `/events/completions` requires bearer; build identity only bridge.py | Misdiagnosed outages | `/health.capabilities` + authenticated `/capabilities`: PID/start, loaded module hashes/build, listeners, route manifest, admin availability, queue/dependency summary |
| `inbox_local.py`, recovery/supersession CLIs | New admin source staged after process started, so live 404 | Learned only when invoking operation | Presentation recovery only | Guarded local capability probe and exact build check BEFORE operation; public listener still rejects local-admin routes |
| `TrayController.cs`, `Stop-Bridge.ps1` | Old process survives shutdown timeout | Tray previously disposed its job even after timeout | Risk of killing work | Verified PID and loaded module identity; timeout now retains old process and refuses replacement; force-stop script disabled; no active-turn restart performed |
| Inbox V1 queue/native/Firefox verifier | NEEDS_REVIEW/FAILED_PERMANENT/no Send proof | Exact hash/one-Send proof and no-blind-resend, queue retained | Must never gate planning | Those proofs unchanged; no browser dependency in ingestion/scan. Queue remains degraded, honestly reported |
| Exact stale watchdog / `inbox_supersession.py` | Unattempted queued nudge ahead of seq94 | Audited one-target policy already implemented in #81, but unloaded | Blocks that presentation recovery | Preserve immutable proof + atomic SUPERSEDED audit, never DELIVERED. Capability/client tests pass; live activation/cancellation still pending |
| Direct GitHub #45 | Inbox/bridge down | Independent comments and Jarvis ACKs | Not transport-dependent | Durable unique signal marker + exact readback; ambiguous POST never resent. New synthetic signal posted/read back; its Jarvis ACK still outstanding |
| Usage exhaustion | Terminal relay issue, unfinished task, reset embedded in prose | State classified but original request_json cleared | Yes | Preserve exact request/hash/error and reset metadata in same terminal transaction; RETRY_WAIT / RESET_TIME_REQUIRED / RESET_ZONE_REQUIRED distinct. No guessed timezone or automatic duplicate retry; actual Jarvis retry scheduler acceptance remains required |
| VM to Windows / Funnel | Local service healthy but Tailscale transport unavailable | #84 diagnosed separate layers | Must not gate GitHub | Independent loopback versus remote status; no VPN/firewall/reset changes. Remote test/result still requested from Jarvis |

Jarvis VM paths, current process hashes, cursor transaction implementation, #45 polling/ACK durability, and actual successor creation code cannot be certified from Windows: no shared checkout or VM connection was available. This is an explicit boundary, not an inference that the VM is broken or fixed.

## Implemented contract

`tools/relay_reliability/contract.json` is the machine-readable Windows/Jarvis interface and acceptance checklist. `continuity.py` is an executable reference, not a second inference engine. `watch.py` can run an explicitly installed read-only observer. It has no task-creation/browser-dispatch facility.

- GitHub author/private-repo/envelope and exact result SHA checks precede admission. Multipart chunks/manifests and full result hashes are verified. Receipts retain repository/comment ID/exact body/hash; request/result identity is canonical. Same terminal content in another comment aliases the result, conflicting content is quarantined.
- Local positive sequence is transactional and immutable. Out-of-order older issues are backfilled, never skipped against a cursor. Later bridge numbering only enriches a nullable separate column; conflict rejects without changing local ordering. The Windows provisional/highest-seen invariant does not replace canonical identity.
- Polls have bounded full pagination and explicit errors on bounds/fetch/identity problems. Valid issues survive unrelated quarantine; an unexpected process/transaction failure rolls back the poll. Corrupt stores are preserved with an ERROR sidecar, never replaced by an empty cursor.
- Read-only continuity scan uses GitHub issue/result state, latest creation order, durable first-verified-result grace and pending request/retry state. Intentional pause is checked first; no AW17 nudge or task is created. Senior-review intents have a unique parent key, but **actual Jarvis successor exactly-once acceptance is not yet proven**.
- Worker health contains build/PID, last success/error, backlog/high-water, dependencies, retry state and explicit pause. Unavailable Inbox/bridge yields DEGRADED while `continuity_healthy=true` can remain true. Integrity quarantine makes ingestion DEGRADED/actionable, not success. Bounded backoff, durable unique errors/intents, and exact signal markers suppress repeated alerts.
- Snapshot/status files use fsync + atomic replace. The versioned source bundle and hash manifest contain no runtime state/secrets. `stage.py` defaults read-only and requires a reviewed current fingerprint before source-only staging. It never restarts a process or opens delivery databases.

## Fault injection / regression acceptance

**28 focused tests + 67 relay/completion/outbound tests + 26 supersession tests + 31 recovery tests = 152 Python tests; one compiled C# tray policy suite.** Focused tests use actual production module interfaces and temporary stores/listeners. No inference is run. The 14 cases below are reference/Windows acceptance, not a substitute for the deployed Jarvis matrix.

| Required fault | Evidence / result |
|---|---|
| 1 completions404 | Reference has no discovery dependency; actual ephemeral HTTP404 in #87 smoke; one result ingested |
| 2 bridge unreachable | Fault state cannot change result admission/order; result retained |
| 3 VM route lost, localhost healthy | Independent dependency state, GitHub discovery unchanged; real VM-path test remains Jarvis-required |
| 4 stale old PID | Capability PID/build mismatch rejects; production-shared C# exit-confirmation rejects live PID; no replacement/kill |
| 5 Inbox unavailable | Ingestion healthy, presentation degraded; real GitHub smoke uses injected Inbox outage |
| 6 NEEDS_REVIEW | Does not gate scan/unique senior-review intent; no resend |
| 7 stale watchdog ahead | No Inbox queue dependency in scan; unique intent still forms; existing audited supersession 26-test suite passes |
| 8 duplicate result/poll | Same receipt/result committed once across restart; direct signal reconciles exact comment |
| 9 out-of-order results | Older result admitted after newer; bridge enrichment cannot overwrite local order |
| 10 fetch/commit crash | Injected exception and real child-process `_exit` during transaction; rollback/re-poll yields one result |
| 11 corrupt/partial state | Integrity/schema failure preserves file and emits ERROR; corrupt worker health also rejects |
| 12 usageLimitExceeded/reset | Prompt/hash/raw error and structured/reported reset retained; pending retry suppresses successor, timezone ambiguity stays explicit |
| 13 restoration | HTTP dependency404 to200; health DEGRADED toHEALTHY, same one result and one intent |
| 14 AW16 pause | INTENTIONAL_PAUSE, successor_permitted=false; staged Windows dispatch guard retains conventional Brain Age requests queued without dispatch |

Additional tests: production-generated Unicode/multipart interoperability, edited comment rejection, request collision quarantine, bridge sequence conflict, uncertain direct POST exact readback/no resend, actual authenticated capability HTTP and public-admin isolation, durable worker health/recovery. The first crash/savepoint test failure was fixed and rerun; not hidden or counted as a pass before correction.

## Real GitHub end-to-end evidence

Reuse #87 result comment **6215141578**, SHA256 `f2b0492bd67b040a63250aace1607534cb4c2577e7a5e9446187b74bbc6d67a1`. Independent #45 signal **6215143552** was posted and read back exactly, then reused without another POST. These are tagged synthetic/non-task issues, so the production `[CODEX RELAY]` dispatcher does not launch them.

| Phase | Result/high-water | Health | Continuity / presentation |
|---|---|---|---|
| Before clean smoke | 0 / 0 | No prior poll | No inference permitted |
| HTTP404 + Inbox outage | 1 / 1 | DEGRADED, ingestion HEALTHY | continuity_healthy=true, inbox_delivery_degraded=true |
| Restart + NEEDS_REVIEW | 1 / 1 | DEGRADED | Same receipt/result, one senior-review intent, no successor |
| Dependency200 + Inbox restored (injected) | 1 / 1 | HEALTHY | continuity_healthy=true, inbox_delivery_degraded=false |
| Real authoritative backfill on resume | 82 / 82 | DEGRADED/actionable issue72 identity conflict | AW16 INTENTIONAL_PAUSE; valid new results not starved |

The fault endpoint and Inbox statuses are injected; no production listener was disabled, restored or misrepresented. Real GitHub fetch/comment identity and durable restart are actual. **The deployed Jarvis result_poller and its new #45 ACK are not yet validated.** Local evidence: `local/relay-reliability/clean-wire/smoke.json`, `smoke-initial-eventual-consistency.json`, and `authoritative-readonly.sqlite3.health.json`/private SQLite. Private prompts/results/queues and credentials are not committed.

## Live activation, network and queue state

Read-only health shows PID **24184**, original bridge source `f2cc0cca8c661e2fe601f37050979988c3663da0d1b66672baf0d9a8f4179f65`, no loaded capability manifest, active current hardening turn. Therefore **restart_allowed_now=false**. No restart/force-stop/admin POST was attempted. Source staging is not activation.

#84 is authoritative: loopback `/health`200, unauthenticated exact `/events/completions?after=0`401, wrong `/completions`404. AW14/15 Windows records existed (112/115). Tailscale offline/socket10013 and active PIA split-default routes support remote transport/policy degradation; **VPN causation remains plausible, unproven**. No new VM/network claim is made. Senior's #45 comment6222460817 requests the exact authenticated VM-path test; Jarvis ACK6222467808 confirms receipt, not a completed test result.

Live queue hash remains `5c55a0bcbef5cd39b69738a1fc90743a020d173ceca306176807c4a2099c14f8`. Watchdog `jarvis-continuity-watchdog:1fe09e7e9c1dec11d6dbd2385e0fb9cb8697ab85ede379f0308cd467b361ec52` is QUEUED/attempt0/no claim/no outcome; no supersession audit. Seq94 is FAILED_PERMANENT/attempt3. The watchdog remains the sole QUEUED preflight blocker for that **presentation recovery only**; it does not block GitHub discovery or authorize Brain Age continuation. No queue, ACK, cursor, request, or save evidence was fabricated.

## Exact remaining acceptance / next action

1. Jarvis must consume the contract from the committed `codex/brainage` source, provide deployed code hashes, run its own actual poller/planner 14-case matrix, ingest existing #87 comment6215141578 without the Windows path, prove restart/dedupe/backfill/usage retry and intentional AW16 pause, and ACK signal6215143552 through #45. No new Brain Age request is authorized.
2. At an **idle** boundary (live `turn_active=false`, no active async request), safely stop the old tray/owned bridge and launch the updated `bridge/Tray-Controller.ps1`; the old already-compiled tray cannot acquire new C# semantics merely by staging source. The updated controller refuses a surviving old PID, validates new owned PID and module manifest, and does not declare Ready on a stale build. This active turn cannot perform that post-terminal operation itself, and no accessible independent managed control channel was available. Do not kill PID24184 or force-close an active tray.
3. Run `python dev/tools/relay_reliability/check_activation.py --bridge bridge`. Require exact loaded hashes/admin capability; then review `python bridge/inbox-v1/supersede_watchdog.py` proof/fingerprint and invoke only its existing explicitly reviewed one-target supersession, if still eligible. Do not rearm/send seq94 here. Activation and actual SUPERSEDED audit remain pending, not a claimed cleanup.
4. Compare Windows loopback and Jarvis's exact authenticated remote status separately; keep GitHub continuity running regardless of remote failure. Prove restored dependency telemetry in deployed workers, no cursor/result disappearance, and no duplicate successor. Only a separate senior decision can clear the AW17 gate.

Stop after hardening. Brain Age remains paused after AW16.
