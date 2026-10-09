# Task S — known-glyph adapter into the mapped Decuma boundary

**FULL PASS, 2026-10-09.** Two fresh-process restores independently reproduced `2 ? 4`, return `0 ? 0`, group counts `(0,1)` after each stroke and metric `500 ? 249`. Trial A used 9/5 points; Trial B used 5/3. Recognition stopped before any exercise answer consumer. This proves only the specified two-stroke digit in this initialized title context.

## Identity and starting state

- Branch: `codex/brainage`; predecessor Task R: `ea70dd34d555b155e48b5353378029f1e547666c`.
- ROM SHA-1: `b8a105bacc3234dede8d4465df0869f2b922a0e2`.
- Framework baseline: `3a57236bb23d25dcb4caad7d58d733311062ff5e`.
- Checkpoint: `local/task-g/session-001/11-answer-01-63/checkpoint.state`, copied separately into each trial. Its SHA-256 is in [trial metadata](BrainAge_TaskS_Trials.json).
- Source Flash: that checkpoint directory's `after.sav`; independent `initial.sav` and `disposable.sav` per process.
- The preserved original problem is `11 - 7`. The entry guard checks expected value 4, previous correct count 1 and phase 1. No touch command is issued.
- Source checkpoint/save bytes were compared again after each trial and remained unchanged.

## Invocation mechanism and isolation

No suitable existing guest-call API was found. Debug register access is read-only, and the original worker depends on a queue/thread wakeup. Instead, an opt-in, fixed-target interpreter diagnostic intercepts ARM9 entry `0x02026510`, saves the full private interpreter CPU state, resolves the initialized handwriting objects and directly redirects interpretation to the actual `0x020A41A0` target. This is mechanism C, **not execution of the original worker callsite `0x02051AF4`**.

The synthetic LR is `0x02051AF8`. The hook intercepts this address before its guest instruction executes. It then calls only the already-mapped metric accessor `0x020A3FB8`, using `(context, 1, 0, slot+0x144)`, and similarly captures its return. The ordered calls are recognition(0), metric(0), recognition(1), metric(1). All return synchronously with r0=0.

After the second metric return, the saved CPU state is restored and execution terminally halts. The disposable process is discarded. This is not a resumable guest-call service: elapsed guest time, peripheral state and recognizer mutations are not rolled back. There is no scheduler modification, guest trampoline/code write, ROM patch, generated C edit or general guest-call framework.

The hook rejects entry into `0x020266B4`, `0x02025778`, `0x02025698` or the original accumulator `0x02052424` while active. It verifies SP bounds, a 256-byte stack guard, balanced return SP, callee-saved r4–r11 and a 50-million-cycle bound. The complete exercise object (0xC34 bytes) and manager (0x238 bytes) are identical before/after both trials: count remains 1 and phase remains 1. Neither answer submission nor correctness validation executes. No original exercise is completed.

## Resolved objects and safe storage

All addresses below were independently resolved and verified after each fresh restore; they are run observations, not universal constants.

| Object | Address | Verified allocation/use |
|---|---|---|
| Exercise | `0x020E9A00` | checked/snapshotted 0xC34 bytes |
| Manager | `0x020FA808` | 0x238 bytes; one slot, empty request queue |
| Slot | `0x020FAA50` | 0x370 bytes; mode 0, zero pending points/strokes |
| Initialized context | `0x0211B994` | 0xA350 bytes |
| Points | `0x02125CF4` | 0x4000-byte allocation, slot+0x208 |
| Descriptors | `0x020FC0D0` | 0x100-byte allocation, slot+0x20C |
| Alternate point allocation | `0x02129D04` | 0x4000 bytes, slot+0x1FC; temporary guarded stack |
| Alternate descriptor allocation | `0x020FC1E0` | 0x100 bytes, slot+0x200; first 8 bytes hold output counts |
| Group 0 output | `0x020FAB34` | slot+0xE4, capacity 16 uint16 codes |
| Group 1 output | `0x020FAB54` | slot+0x104, capacity 16 uint16 codes |
| Metric output | `0x020FAB94` | slot+0x144 |

The allocation sizes/stores are statically visible in `0x020531C8`'s initialization chain. Context size helper `0x020A3F08` adds 0x94E0 to helper `0x020A898C`'s 0xE70, giving 0xA350. All spans are dynamically checked for canonical writable main RAM and pairwise non-overlap. The mode-0 idle guard prevents borrowing alternate buffers from an active alternate-mode operation. No queue record or UI-state field is fabricated.

Call SP is `0x0212DCE0`, eight-byte aligned. The lowest observed same-mode SP is `0x0212CE88` (3,672 bytes below entry). Both trials preserve the lower 256-byte guard at `0x02129D04`. Interrupt scheduling remains ordinary; no host timing is used as causal ordering evidence.

## Independent adapter input and output

`tools/task_s/adapter.h` defines a vector of strokes, each a vector of host `{int x, int y}` points. It contains no guest pointers in source data and does not read the original accumulator. Trial A duplicates the supplied known source points according to the Task R reference sampling pattern. Trial B uses these exact host points:

- Stroke 0: `(190,110), (156,91), (121,65), (121,98), (121,130)`.
- Stroke 1: `(173,114), (132,114), (75,114)`.

Conversion is `(x,y) ? (y,255-x)`. The adapter serializes two little-endian uint16 coordinates, stride 4, with no contact field or sentinel. Each descriptor is `{uint32 count, uint32 first_point_pointer}`, stride 8. Trial B stored points are:

- Stroke 0: `(110,65), (91,99), (65,134), (98,134), (130,134)`.
- Stroke 1: `(114,82), (114,123), (114,180)`.

Source bounds are x=0..255, y=0..191; nonempty strokes, at most 32 descriptors and at most 4096 total points. These are storage safety bounds, not proven recognition quality limits. Tests verify rejection outside these bounds. Buffers remain valid for every call and are discarded with the process. Trial A's 56 point bytes and 16 descriptor bytes exactly match Task R's preserved finalized dumps.

## ABI and results

At each recognition entry:

- r0=`0x0211B994`; r1=`0x020FC0D0` then `0x020FC0D8`; r2=0 then 1; r3=`0x020FAB34`.
- `[sp+0..16]` = `16, 0x020FC1E0, 0x020FAB54, 16, 0x020FC1E4`.
- PC=`0x020A41A0`; synthetic LR/return gate=`0x02051AF8`.
- Descriptor bytes, pointed-to data, r0–r3, all five stack arguments and raw context/input/output/stack snapshots are captured before/after each call.

| Run | Points/stroke | Candidates | Recognition returns | Group counts each call | Metric after accessor |
|---|---|---|---|---|---|
| Task R original accumulator | 9 / 5 | `0x0032` ? `0x0034` | 0 / 0 | 0 / 1 | 500 ? 249 |
| Task S A exact adapter replay | 9 / 5 | `0x0032` ? `0x0034` | 0 / 0 | 0 / 1 | 500 ? 249 |
| Task S B deduplicated adapter | 5 / 3 | `0x0032` ? `0x0034` | 0 / 0 | 0 / 1 | 500 ? 249 |

The returned group-1 first uint16 code is the candidate selected by the mapped Task R path; Task S reads this code without executing that consumer. It is not credited as an exercise answer. The metric is **not established as confidence**.

Initial contexts/slots and all compared post-call context/slot snapshots are byte-identical across A/B. The only source-policy change was removing held-sample duplicates: descriptors, point payload length and point pointer for stroke 1 change accordingly. No candidate, group-count, return-status or metric change was observed.

## Exact deliberate write manifest

[Trial metadata](BrainAge_TaskS_Trials.json) contains every write's address, length, before SHA-256 and adapter SHA-256. Local `write-N-before.bin`/`write-N-adapter.bin` retain the bytes. All writes are checked against the resolved permitted allocations and read back.

| Write | Range (inclusive) | Bytes A / B |
|---|---|---|
| Adapter points | A `0x02125CF4..0x02125D2B`; B `0x02125CF4..0x02125D13` | 56 / 32 |
| Descriptors | `0x020FC0D0..0x020FC0DF` | 16 / 16 |
| Stack guard | `0x02129D04..0x02129E03` | 256 / 256 |
| Count initialization, twice | `0x020FC1E0..0x020FC1E7` | 8 each / 8 each |
| Stack ABI arguments, twice | `0x0212DCE0..0x0212DCF3` | 20 each / 20 each |

Seven writes per trial: total write volume 384 bytes A / 360 bytes B; distinct modified ranges cover 356 bytes A / 332 bytes B. No bytes are restored in those disposable input/scratch allocations. Recognition naturally mutates its context, output slot and call stack; those mutations are separately measured, not attributed to the adapter's direct writes.

Net changed main-RAM bytes between entry and final return:

| Region | A | B |
|---|---:|---:|
| Context | 829 | 829 |
| Output slot | 3 | 3 |
| Points | 26 | 15 |
| Descriptors | 3 | 3 |
| Temporary stack | 3325 | 3325 |
| Count scratch | 8 | 8 |
| Title BSS | 2 | 2 |
| Other shared-system byte | 1 | 1 |

The BSS bytes are `0x020D3008` and `0x020D30AC`. Startup module parameters at `0x02000B04` specify BSS `[0x020D2BA0,0x020E6FC0)`; startup `0x0200088C..0x020008A4` clears it after autoload relocation. Treating the entire raw loaded image as live code initially produced a false audit failure; the corrected assertion excludes the proven BSS. The other byte is `0x023FFC3C`; its exact system role was not needed or reverse-engineered. These three bytes change during ordinary execution, not through an adapter write. No unrelated guest-object mutation is required to initiate recognition. Main-RAM image bytes below BSS remain unchanged; the direct write whitelist permits no executable/code region. Generated banks and ROM remain untouched.

## Save safety and validation

Both trials: zero logical save requests, zero accepted Flash commits, zero changed disposable-save bytes. Initial Flash, live final Flash and disk Flash match. For A before/after and B before/after, SHA-256 is:

`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`

Canonical H0 and historical Task G/R evidence are unchanged. The exercise and manager snapshots are identical before/after; count/phase do not advance.

A tiny no-input, 100,000 ARM9-cycle checkpoint smoke compared the preserved Task R executable with the Task S executable with the opt-in hook disabled: identical I/O state, cycle/instruction counts, all 4 MiB main RAM, and save bytes. It issued no touch and made no logical/Flash writes. No custom-host regression or production-host execution was performed. `bc_host.h`, `bc_freehand.h`, `bc_quiz.h` are unchanged.

Preserved Task A, O SDL and R runner hashes were verified unchanged. Task S executable SHA-256: `e592d5e2a2a5b377af445d10a96d894306f30805857fcb1e00f4e1c020dbfe72`.

## Reproduction and artifacts

Requires the existing pinned local framework, generated title artifacts and Task R diagnostic installation. Build separately with `tools/task_s/build.ps1`; it installs only ROM-free hooks into the ignored local framework and writes `build/task-s-runner`.

1. `python tools/task_s/run_trial.py --out local/task-s/<new-A> --variant A`
2. `python tools/task_s/analyze.py --out local/task-s/<new-A>` — stop if A fails.
3. `python tools/task_s/run_trial.py --out local/task-s/<new-B> --variant B`
4. `python tools/task_s/analyze.py --out local/task-s/<new-B>`
5. `python tools/task_s/compare.py --a local/task-s/<new-A> --b local/task-s/<new-B> --out <derived-json>`

Authoritative local evidence: `local/task-s/trial-a-001`, `local/task-s/trial-b-001`; disabled-hook smoke: `local/task-s/disabled-r`, `local/task-s/disabled-s`; narrow static evidence: `local/task-s/static-safety` and existing `local/task-r/static-001/020531C8.txt`. Raw captures, saves, checkpoints and executable remain local/ignored. The committed JSON contains only compact derived metadata and hashes.

## Task T recommendation — design only

The next bounded experiment can expose a narrow initialized-context recognizer service to the custom host, convert captured freehand strokes with this adapter and display the returned digit in native UI, with no Brain Age answer submission or save/progression write. Context lifecycle/reset, threading/ownership, safe return to the host and service scratch ownership must be established for that integration; this terminal diagnostic is not that service. Task T is not implemented or begun.

Unproven: arbitrary drawings, production resampling/normalization, letters/symbols, physical pen parity, standalone initialization, external-title middleware reuse, custom-host integration, save/menu integration. No broad middleware reverse engineering occurred. Approval infrastructure was unchanged; approved escalated commands required no separate human confirmation.
