# Independent post-turn Windows activator

**FULL for arming only. Actual activation and supersession remain deferred until this exact turn is terminal. Brain Age remains paused after AW16.**

## Live arming evidence

- Request: `relay-resilience-post-turn-windows-activation-20261016-01`.
- Scheduled mechanism: current-user, least-privilege, InteractiveToken Windows Task Scheduler task `MuseRelay-PostTurnActivation-20261016-01`, on-demand only, IgnoreNew multiple-instance policy, no recurring trigger.
- Running instance: `{C83B7820-36AC-4A6E-868F-93B9AF611C7A}`; worker PID **214552**, `pythonw.exe`, parent PID2204. Task Scheduler itself identifies engine PID214552 and exact action/arguments. The worker is outside bridge PID24184/Codex's process tree.
- Verified phase: `WAITING_FOR_TERMINAL`, reason `awaiting_exact_turn_terminal`. Current bridge remains PID24184, active through this exact request, loaded source `f2cc0cca8c661e2fe601f37050979988c3663da0d1b66672baf0d9a8f4179f65`. No managed shutdown command has been sent to it.
- Intended hardened module build: `6bb1a688621cc771774b8434c0360031110ecf5af86e2600a0282589e303932d`, bound to authoritative hardening commit `e7746ae8de45a8ca899064e3d3db2f94fa7169d4` and its exact source manifest.
- Re-running ordinary `--arm` was tested: it reads the existing intent/evidence and creates no second task or worker.

## Reuse of existing ownership, not a second relay service

`tools/relay_reliability/post_turn_activation.py` is one bounded scheduled controller. It does not own a listener, token, app-server, alternate relay, inference engine, or gameplay state. It reuses the existing tray (PID280572) and its existing managed stdin channel. The in-memory bridge bearer remains with the tray and is neither read nor copied.

`managed_pipe.cs` enumerates bounded handle/access metadata for those exact PID/start identities, requires one write-only pipe in the verified tray process and a pipe reader in its owned bridge child, and binds the channel by parent/child creation times plus handle identity hash. The live read-only probe identified exactly one channel. The only production command implemented is the existing `{"op":"shutdown","if_idle":true}` line. No unconditional shutdown, process kill, memory-reading, credential extraction, remote-thread injection, or UI operation exists in this adapter.

The authoritative final race guard is the existing bridge's `stop_if_idle()`: it acquires the guest-turn lock nonblocking and closes work admission before shutdown. A new turn winning that race causes refusal; the controller waits/backoffs and independently re-establishes stable idle. No force-kill fallback exists. The old tray's existing recovery starts the hardened Python source with the same token; the controller independently proves old process exit and the resulting new identity/module/capability manifest. It never starts a competing bridge. This does not claim the old already-loaded C# tray itself has hot-reloaded its new source.

## Exact guards

1. Exact original request and Codex turn UUID must be durably `COMPLETED`, with terminal timestamp, no pending request, no other nonterminal relay request, and its GitHub result outbox fully CLOSED with verified comment IDs. Failure/usage-exhaustion does not permit activation.
2. Loopback health must show `turn_active=false`, no active async request, no maintenance/review condition, and relay ready. Four consecutive checks spanning at least15 seconds are required; any busy/unknown sample resets them. Source, old PID/start, tray PID/start/parent and protected inputs must remain exact.
3. The native channel is re-probed and terminal/idle state sampled again immediately before the atomic managed idle command. All commands stay bound to the same original PID/start/channel; at most that one original process can be stopped.
4. Old exit is established by a signaled verified process handle or OS no-such-PID evidence. Access denial/query failure is not exit proof. Timeout fails closed, never kills.
5. New PID/start must differ appropriately, be owned by the same tray, and present exact module hashes/build, source-bound routes, loopback listeners and local supersede capability. Browser delivery must not have become enabled.
6. Only then may the exact audited stale-watchdog operation run. Fresh server provenance/proof hash and queue fingerprint are checked; one admin POST maximum. An ambiguous response causes audit readback only, never another POST. Audit proof/hash, original entry, authorization and SUPERSEDED outcome are verified; attempt count remains0 and delivered_at remains null.
7. Seq94's entire original entry must remain unchanged. Only eligible queue blockers/preflight are reported; no recovery, Send, rearm or readiness-hold release is performed.
8. No AW17 task or gate release is implemented. No bridge/config/queue source is rewritten by the worker. The no-send hold and configuration hashes are protected.

## Durability and idempotence

`bridge/.runtime/post-turn-activation/plan.json` is the exact immutable intent/input binding. `evidence.json` is fsynced/atomically replaced and records idle samples, old/new process identities, capability manifest, local/remote status, before/after watchdog/audit, seq94 preflight, phases and failures. A file lock plus Scheduler IgnoreNew prevents concurrent workers. Completed or post-action failed states do not automatically re-execute. Six-hour admission deadline, bounded process/activation waits and eight-hour task execution limit fail closed.

An initial pre-effect worker safely rejected ancestry because the protected scheduler service parent could not be queried by the user process. Its plan/evidence/registration remain under `pre-effect-failure-001/`; it sent no shutdown or admin operation. A narrowly guarded, explicit pre-effect repair verified: only ARMED/FAILED phases, exact ancestry-only rejection, no running previous instance, same still-active original request/bridge, unchanged protected inputs/queue and no supersession. The replacement proof binds Task Scheduler's exact instance/action/InteractiveToken/engine PID to the worker instead of guessing a protected parent's image. The same one-shot task/intent was resumed, not a second activation permit. Ordinary `--arm` never performs that repair automatically.

## Reporting and evidence

The existing credentialed `GHClient` path and durable exact-comment `signal` outbox report a concise `[WINDOWS-ACTIVATION-RESULT]` to private relay issue #45 after terminal success/failure. The same Windows user's existing gh credential store is used; no token/credential is exported or new transport installed. The pre-effect failure successfully reported as comment **6223638880**, proving this existing reporting path is usable. Terminal phase-specific identities allow a distinct final result without rewriting or duplicating that earlier evidence. Reporting failure is retained locally; uncertain POSTs are not blindly repeated.

Primary live artifacts (not committed):

- `bridge/.runtime/post-turn-activation/plan.json`
- `bridge/.runtime/post-turn-activation/evidence.json`
- `bridge/.runtime/post-turn-activation/registration.json`
- `bridge/.runtime/post-turn-activation/report.sqlite3`
- `bridge/.runtime/post-turn-activation/pre-effect-failure-001/`

Remote/VM reachability is recorded separately as not tested by this Windows controller, never inferred from successful localhost health. No automatic reliability-gate release follows.

## Tests

12 focused tests pass, including independent terminal/idle/capability mutations, stable admission, a post-check new-turn race, no action for an active/wrong-identity turn, source tamper, idempotent arming, complete synthetic success, target-change rejection and uncertain admin-response readback without resend. 28 continuity regressions pass. The native adapter's own isolated fixture proves the fixed managed line is delivered through a duplicated owned write handle; the live channel was probed without writing. An earlier blocked pipe-name-query experiment was removed; only its hung disposable fixture executable was stopped. No bridge/tray/Codex process was killed.

This turn reports **ARMED**, not activation success. Let the worker observe terminal completion after this response; do not start another task to make it active again before it can establish idle.
