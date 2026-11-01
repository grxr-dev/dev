# #111: stop recovery-helper console flashes

The concrete launch defect was in `finish_repair.py`: its GitHub CLI lookups,
posts and two ten-second polling loops used `subprocess.run` without
`CREATE_NO_WINDOW`. A `pythonw.exe` scheduler parent has no console to inherit;
launching a console child that way can display a short-lived console window.
All four sites now set the Windows windowless flag. Five focused tests pass.

The #110 helper's read-only delivery-proof polling ran after receipt commit,
ending at2026-11-01T22:25:22.824Z. Its ten-second cadence and source launch defect
match the reported symptom. It had already finished by this diagnostic: PID1200
absent, scheduled task disabled, zero triggers, last result0. It was not restarted
or rearmed. No historical GUI/process-start trace of a specific reported window
was available, so attribution of every past flash is not claimed as direct visual
observation. WMI start-event access was denied and Task Scheduler operational
history was disabled; neither auditing nor permissions was changed.

A35-second live process capture did find repeated bridge GitHub CLI/conhost starts
about11seconds apart (22:28:13.8,24.8,35.7UTC; parent bridge16660). These must not
be mistaken for the completed helper: the loaded bridge `github_bus.py` matches
disk and already uses `CREATE_NO_WINDOW`. The original tray is also hidden and
starts the bridge with `CreateNoWindow=true`. Required polling remains enabled.
No unrelated tasks, persistent command prompts or services were killed/disabled.

## Verification

- Five no-network tests cover all four corrected CLI paths and the existing
  bridge's already-windowless GitHub client.
- A controlled windowless Python probe ran the corrected real read-only comment
  GET three times, roughly10seconds apart; all matched the requested comment.
  The probe exited normally and made no GitHub write or Inbox delivery.
- During35seconds spanning those calls and normal bridge polling, new processes
  were repeatedly sampled: zero new `cmd.exe` launches and zero nonzero process
  main-window handles. Hidden conhost processes still occurred, which is not by
  itself evidence of a visible popup. No screenshots/pixel observation was made;
  sampling can miss an exceptionally short-lived window. This is process/window
  metadata and verified launch-flag evidence, not a claim of direct visual proof.
- Bridge16660, original tray37780 and Codex RPC remained alive/healthy. Ports8766,
  8767 and127.0.0.1:18741 each remain owned by the same bridge. No restart, duplicate
  bridge, Send, rearm or recovery was performed.
- Exact before/after hashes match for the historical queue, future queue, native
  outcome journal, historical HOLD, binding and future-lane config. Seq133 remains
  DELIVERED/attempt1. Windows future entries remain130–133;134/135 are absent.

Runtime-only redacted evidence is under
`bridge/.runtime/console-flash-111/`: `before-live.json`, `after-live.json`,
`hidden-read-result.json`, `final-audit.json` and original helper-source backup.
No raw command line, token or message body was logged. No owner action/reload is
required. Production sealed components were not edited; only the inactive
maintenance helper and its regression test/report changed.

## Separate VM read-only status

There is no new independent VM alignment/cursor proof in the inspected #45
comments. Last explicit Jarvis status6564542736 was OLD identity/seal and cursor132.
Comment6564758253 proves the Windows operator receipt only. Senior comment
6564810393 says recent operational messages were withheld by a Jarvis tool-output
safety check; generic auto-ACKs do not prove alignment. No safety check was bypassed,
VM configuration changed, or further relay repair attempted in this desktop task.
