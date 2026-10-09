# Brain Age Task H: instruction-only restart recognition check

Date: 2026-10-09. **Blocked within the authorized route.** The completed
Task G save reloads exactly and AAA is recognized. Four picture-instruction
More acknowledgements lead to a blank **Koala** drawing canvas, with Select
disabled and only Erase otherwise visible. No calendar/menu or normal
Back/Skip acknowledgement is exposed. Stopped immediately without drawing
or submitting anything. Visible exercise/stamp recognition remains unverified.

## Recovery and preserved baseline

Used existing `dev`, branch `codex/brainage`, starting at Task G
`5ddb5fa3901f2ec684cfa4737fea1dc65bea5b92`. Framework remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`; existing runner, configuration,
FreeBIOS/generated firmware/direct boot and Task A/C observers unchanged.
No rebuild, new instrumentation, save-state manipulation, ROM/generated-C
edit, coverage work, second exercise or alternate date.

Fresh source: `local/task-g/session-001/51-completed-quiet/after.sav`,
262144 bytes, SHA-256 **H0**:
`2531e8a54ab0ceabc65f23035c8c02064d5a7c4c9cc2042c38e1eed0aace3ed1`.
Independently checked before launch and again after the experiment; unchanged.
All Task G evidence preserved. New isolated output: `local/task-h/restart-001/`.
Used `tools/task_g/restart.py` and `capture.py` without modifying either.
Fresh runner loads an ordinary copied save, **no savestate import**.
The launch helper verifies ROM SHA-1
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

Existing `NDS_TASK_F_RTC_PLUS_ONE_DAY=1` gives actual guest RTC
**2024-01-02 12:00:00**, independently recorded before guest instructions.
Raw RTC registers: `[0x24,0x01,0x02,0x02,0x52,0x00,0x00]`, status1 `0x02`.
Host clock unchanged. All checkpoints remain January 2; final RTC 12:00:40.

Immediate full reload exactly H0. Passive startup and Daily Training entry
have zero logical write requests, zero Flash commits and unchanged H0.
Profile-selection UI shows **AAA / Brain Age 35**, alongside three new-file
buttons. Selected existing AAA normally once, without recreation.

## Known profile-entry operation, separate from instructions

One complete ARM9 API at `0x0200DE78`, immediate callsite `0x0202D744`
(LR `0x0202D748`), source `0x020E95FC`, target `0x7140`, length **48**.
API system cycle **535537866**, ARM9 instruction **110441962**.
One 48-byte transport through staging `0x020D4F60`, shared request
`0x020D4CE0`; submit `0x0200E080`, FIFO send `0x020091B0`, ARM7 receive
`0x037FE230`, worker `0x03802F48`. FIFO word `0x1EB`.
Stage cycles respectively **535538062**, **535538148**, **535538308**,
**535538873**. Payload identity is independently checked at all stages.

Writing Flash tx **259**, byte sequences **1..48**, offsets
`0x7140..0x716F`, command `0x0A`, commit cycles **535540385..535546026**.
Both carried command and byte origins are ARM7 ARM-mode Tier-3 PC
`0x038032B8`; host commit path `flash_spi_write`.
**48 accepted commits, 18 changed bytes**. Net changed ranges, inclusive:
`0x7140`, `0x7144`, `0x7146..0x7148`, `0x7152`, `0x7154`, `0x7156`,
`0x715A`, `0x7160..0x7166`, `0x716E..0x716F`.

Post-entry SHA-256 **H1**:
`2eab9dd70f7cf659fcc90a134931a4cb466628f04de70653c0fae7434065fcfa`.
This exactly matches Task G's independent fresh-restart entry result.
Stable post-entry UI: **Hello!**, More enabled; system cycle 665196544.
The operation is fully complete before instruction progression.

## Each dialogue/instruction boundary measured separately

All More/Next acknowledgements below use the real UI raw touch `(240,152)`.
Every action has a full before/after image, Flash snapshot/hash, logical and
physical trace capture, CPU/RTC timing and local loadable checkpoint.
At each boundary below the cumulative enclosing API count is **1 -> 1**:
**zero new logical requests, zero Flash commits, zero changed bytes**;
before and after hashes both **H1**. No pen path or drawing-area tap supplied.

| Capture | Exact semantic action / resulting UI | System cycle before -> after |
| --- | --- | --- |
| 04-hello-more | More from Hello; cold-weather greeting | 665196544 -> 765572574 |
| 05-greeting-more | More; repeat-return greeting, Next enabled | 765572574 -> 865733207 |
| 06-picture-introduction | Next; attention/listening instruction, More enabled | 865733207 -> 965952870 |
| 07-picture-description-rules | More; instruction to draw described pictures on the right screen | 965952870 -> 1066173084 |
| 08-picture-comparison-rules | More; instruction specifies three pictures in succession | 1066173084 -> 1166173129 |
| 09-picture-prompt-boundary | More; explanation of comparing drawings with supplied versions | 1166173129 -> 1266225152 |
| 10-picture-ready-boundary | More from comparison explanation; actual Koala drawing prompt and blank canvas | 1266225152 -> 1366431744 |

Capture names are labels, not proof of UI states; the inspected framebuffer
images and the table record the actual screens. In particular, the final
screen is **not** another readiness instruction or the home menu.

## Exact stop condition and recognition limitation

Final left screen displays AAA and asks for a drawing of **Koala**. Right
screen has a blank bordered drawing canvas, **Select greyed out/disabled**,
and **Erase**. No More, Next, OK, Back, Skip or menu navigation is visible.
The last allowed instruction acknowledgement **automatically exposes the
activity interface**; no separate Start button was pressed. This distinction
is preserved rather than claiming the drawing interface never appeared.

**Actual drawing begun: no** in the sense of zero supplied drawing strokes
or drawing-area touches; **drawing submission: none**. No Select/Erase
action, blank submission, cancellation experiment, hardware-button probing,
picture completion or second exercise performed. Stopped at the first
concrete drawing/submission boundary, as authorized by Task H.

The introduction text can be advanced without drawing, but it does **not**
clear into the calendar/menu. Normal visible continuation is gated at the
drawing/submission UI. No claim that every untested hidden navigation path
is impossible; only the observed normal instruction-only route is blocked.
No picture-logic reverse engineering or game-logic bypass attempted.

Consequently, post-relaunch visible targets are all **unreachable** here:

- January-2 training stamp/calendar mark.
- Calculations x20 completion marker, if the UI exposes one.
- Retained 22-second record/result, if immediately available without exercise.
- Relevant post-exercise unlock/menu changes; none inspectable on this route.

**Task G's exercise persistence remains proven. Visible post-relaunch
exercise/stamp recognition is still not independently proven.** Existing AAA
recognition, byte-exact save reload and preserved exercise/stamp ranges must
not be substituted for an unobserved calendar/result UI.

## Instruction persistence and artifact audit

Instructions themselves: **0 logical operations, 0 submissions, 0 Flash
commits, 0 changed bytes/ranges**. No instruction-associated requester to
classify. Whole Task H run: only the known 48-byte profile-entry operation.
Independent Task E auditor verifies source/page/FIFO/ARM7/physical payload
correspondence, complete transaction and old-byte replay of all 262144 bytes.
Full replay equals final live Flash and ordinary on-disk save, both H1.
All Task G exercise/stamp-written spans remain byte-for-byte unchanged.
Last Flash event system cycle 535546026; final 1366431744, a quiet difference
of **830885718 system cycles**. No unfinished save was truncated.

No helper changes needed; only this ROM-free report is new. Local audit JSON
contains phase counts/timings/hashes, physical correlation and blocker notes;
raw game-derived evidence stays ignored. Artifact checks passed, without
additional gameplay or validation/performance matrices.

Normal sandbox execution failed before command execution with the exact
existing error:

```text
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
```

Supported individually reviewed `require_escalated` execution then worked
without human approvals or repeated Graham prompts. No full-access mode,
approval-policy weakening or approval/bridge infrastructure edits. The
existing supported bundled apply_patch path handles workspace reparse paths.

Local evidence:

- `local/task-h/restart-001/`: initial copied H0, verified reload, isolated
  process/session, all before/after images/saves, traces, debug logs and states.
- `local/task-h/restart-001/03-select-AAA/`: completed known return write.
- `local/task-h/restart-001/10-picture-ready-boundary/`: exact blocker UI,
  untouched blank canvas, H1 and preserved checkpoint.
- `local/task-h/recognition-audit.json`: independent complete replay and
  per-action request counts, timing and full hashes.

Representative commands (existing output directories must not be overwritten):

```powershell
python tools/task_g/restart.py --source local/task-g/session-001/51-completed-quiet --out local/task-h/restart-001 --port 19855
python tools/task_g/capture.py --out local/task-h/restart-001 --label 00-reloaded --cycles 0 --savestate
python tools/task_g/capture.py --out local/task-h/restart-001 --label 01-startup --cycles 730000000 --savestate
python tools/task_g/capture.py --out local/task-h/restart-001 --label 02-daily-training --tap 144 96 --cycles 300000000 --savestate
python tools/task_g/capture.py --out local/task-h/restart-001 --label 03-select-AAA --tap 195 80 --cycles 300000000 --savestate
python tools/task_g/capture.py --out local/task-h/restart-001 --label 10-picture-ready-boundary --tap 240 152 --cycles 200000000 --savestate
```

The final command represents the last measured acknowledgement, **not** a
blind jump from profile entry: follow the separately measured dialogue order
above, inspect each actual screen, and stop at the blank Koala canvas.
The verified paused Task H runner is terminated only after complete evidence
preservation; its loadable blocker checkpoint survives. No copyrighted
artifacts are staged or pushed. No Task G evidence changed.

**STOP AFTER TASK H. No drawing, second exercise or Task I.**
