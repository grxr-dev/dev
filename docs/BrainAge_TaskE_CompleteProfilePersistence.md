# Brain Age Task E: completed profile-confirmation save and restart

Date: 2026-10-09. **Success: full confirmation sequence captured; a fresh
runner recognizes AAA with Brain Age 35 from the completed save.**

## Recovery and unchanged baseline

Used the existing `dev` checkout on `codex/brainage`, starting at Task D
`a29243cbc10eac9a709f43d14b60fe6924bad14d`. Public ndsrecomp remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. Reused the existing headless
`build/task-a-runner/nds_runner.exe` and unchanged Task A/B/C logical/Flash
observers, configuration, FreeBIOS, generated firmware, direct boot and
forced interpreter selection. No rebuild, generated-C edit or coverage work.

Restored `local/task-d/route-001/13-confirm-profile-review/checkpoint.state`
into `local/task-e/aaa-001/`. State SHA-256:
`65cf8c0ce5a80b35aa455c145fc5b706e0e727c543367a2216acf8448b05651e`.
CPU control, cycles and instruction counts matched the source. Visible
review: handwritten **AAA**, birthday **1985-01-01**, Select/Revise enabled,
Select not pressed. ARM9 cycles 13612032288; ARM7/system 6806016144.
New logical/physical sequences and counts start at zero; historical generic
initialization is not recounted. Marker remains at `0x180`.

ROM SHA-1 was independently checked by the restore and fresh-launch helpers:
`b8a105bacc3234dede8d4465df0869f2b922a0e2`. Task D evidence is unchanged.

Full 262144-byte Flash identities:

- **H0**, pre-confirmation:
  `f8310763e5c388ceeb82b520c20fcd88e35a3c93af14db7d3dcaebcec292ede0`.
- **HA**, completed AAA:
  `fa9c6b3253574bac7d2969943ff29175022264e6cb1e190a2b963e1cd499c40a`.
- **HB**, optional completed BBB:
  `81386ff2f34a5280955844b2ebdae29c1b74eec1dfab879250255ef4e64c376f`.

## Exactly one confirmation and automatic completion

Pressed Select once, raw touch `(240,152)`, held approximately 3000000 ARM9
cycles then released. Ran a bounded 300000000-ARM9-cycle observation without
Task D's first-page stop, then waited another 200000000 cycles without input.
No subsequent More, profile screen, exercise or menu was selected in this
confirmation session.

First stable automatic result: left screen says "Done! I'll now calculate
your brain age." Right screen shows **Your brain age is 35**, More enabled.
It remains at that screen through the quiet interval; More is not pressed.

Eight enclosing write API operations and 21 transport submissions complete.
The last actual Flash commit is at system cycle **6843999335**. Final quiet
checkpoint: ARM9 **14112033280**, ARM7/system **7056016640**, giving
**212017305 system cycles with no subsequent logical/Flash event**. The
second 200000000-cycle capture has zero requests/commits/changes, and HA is
unchanged. All captured API payload lengths are fully accounted for by
completed transport transactions; no observed operation remains partial.
The final shared-request word at +0 is zero. No new return/queue tracing was
needed; complete payload accounting, quiet tracing and stable waiting UI are
the completion evidence.

## Primary 1792-byte operation

Immediate ARM9 callsite **`0x0202E8E8`**, LR **`0x0202E8EC`**; API boundary
**`0x0200DE78`**. Source **`0x020E8E94`**, target **`0x600`**, length
**1792 (`0x700`) bytes**. API entry: local event 1, system cycle 6806828215,
instruction 1014041263.

Actual segmentation is exactly **7 x 256-byte submissions**, contiguous
`0x600..0xCFF`. All stage through `0x020D4F60` and shared request
`0x020D4CE0`. For every page the auditor verifies:

1. page equals the corresponding slice of the enclosing API source;
2. submit/send/receive/ARM7-worker offsets, lengths, pointer and payload match;
3. FIFO send/receive both carry `0x1EB`;
4. the physical transaction commits exactly that page, with its final-byte
   `last` flag set;
5. old-byte replay agrees with the final full live Flash image.

All rows below use deterministic system-cycle timestamps. Logical boundary
PCs remain submit ARM9 `0x0200E080`, send ARM9 `0x020091B0`, receive ARM7
`0x037FE230`, worker ARM7 `0x03802F48`.

| Page offset | Submit | FIFO send | FIFO receive | ARM7 worker | Flash transaction | Byte sequences |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `0x600` | 6806828733 | 6806828819 | 6806828992 | 6806829557 | 5 | 1..256 |
| `0x700` | 6807738392 | 6807738478 | 6807738626 | 6807739191 | 11 | 257..512 |
| `0x800` | 6808650054 | 6808650140 | 6808650307 | 6808650872 | 17 | 513..768 |
| `0x900` | 6809561708 | 6809561794 | 6809561948 | 6809562513 | 23 | 769..1024 |
| `0xA00` | 6810504889 | 6810504975 | 6810505121 | 6810505686 | 29 | 1025..1280 |
| `0xB00` | 6811414839 | 6811414925 | 6811415106 | 6811415671 | 35 | 1281..1536 |
| `0xC00` | 6812325476 | 6812325562 | 6812325708 | 6812326273 | 41 | 1537..1792 |

Primary byte commits span system cycles **6806831069..6812358386**. Full
per-stage instruction ordinals, page hashes and per-transaction commit times
are in local `complete-save-audit.json`, not committed raw captures.

## Additional confirmation-triggered operations

**Seven additional enclosing API operations**, in this exact order. Every
entry uses the same API `0x0200DE78`; callsites are the captured ARM LR minus
four, not invented symbol names. No deeper caller-chain investigation.

| Operation | ARM9 callsite | Target | Length | Source | API system cycle | Segmentation / writing transactions | Net changed bytes |
| --- | --- | --- | ---: | --- | ---: | --- | ---: |
| 1 primary | `0x0202E8E8` | `0x600` | 1792 | `0x020E8E94` | 6806828215 | 7x256; 5,11,17,23,29,35,41 | 1778 |
| 2 mirror | `0x0202E908` | `0x20600` | 1792 | `0x020E8E94` | 6813236564 | 7x256; 47,53,59,65,71,77,83 | 1778 |
| 3 small record | `0x0202EAF0` | `0x100` | 16 | `0x020E8E60` | 6819665954 | 16; 91 | 11 |
| 4 paired record | `0x0202EB10` | `0x20100` | 16 | `0x020E8E60` | 6820517422 | 16; 97 | 11 |
| 5 block | `0x0202DD88` | `0x200` | 428 | `0x020E9818` | 6840443377 | 256+172; 105,111 | 5 |
| 6 small record | `0x0202E018` | `0x1B00` | 32 | `0x020E95B8` | 6842267429 | 32; 119 | 31 |
| 7 paired record | `0x0202E038` | `0x21B00` | 32 | `0x020E95B8` | 6843124189 | 32; 125 | 31 |
| 8 record | `0x0202D744` | `0x7000` | 48 | `0x020E95FC` | 6843991203 | 48; 133 | 10 |

The two 1792-byte regions are byte-identical copies separated by `0x20000`.
The 16-byte and 32-byte pairs also match exactly at that separation. The
428-byte block and 48-byte record have no additional mirror write in this
capture. Small records are supported as accompanying profile/setup
bookkeeping; exact field purposes, checksums, indices and commit flags are
not assigned. No complete record layout was decoded.

## Complete Flash diff

- Baseline H0 -> completed HA.
- **4156 accepted one-byte commits**, including **501 unchanged-value bytes**.
- **3655 net changed bytes**, also 3655 changed-byte commits because these
  written spans do not overlap.
- **8 enclosing API operations**, **21 submissions**, **21 writing Flash
  transactions**. SPI transaction IDs include intervening nonwriting SPI
  activity; ID 133 does not mean 133 writing transactions.
- Every command is `0x0A`. Carried command and byte origins are ARM7
  **`0x038032B8`**, ARM mode, Tier-3. Host commit path: `flash_spi_write`.
- Full committed ranges, inclusive: `0x100..0x10F`, `0x200..0x3AB`,
  `0x600..0xCFF`, `0x1B00..0x1B1F`, `0x7000..0x702F`,
  `0x20100..0x2010F`, `0x20600..0x20CFF`, `0x21B00..0x21B1F`.

All **50 contiguous value-changing ranges**, inclusive, are specified by
this compact exact list:

1. `0x100..0x103`, `0x107..0x108`, `0x10A..0x10C`, `0x10E..0x10F`,
   **and each of those ranges plus `0x20000`**.
2. `0x200`, `0x2DC`, `0x390`, `0x3AA..0x3AB`.
3. `0x600..0x613`, `0x615..0x616`, `0x618..0x653`, `0x655..0x66A`,
   `0x66C..0x684`, `0x686..0x690`, `0x692..0x697`, `0x699..0x6A4`,
   `0x6A6..0x6D3`, `0x6D5..0x6DF`, `0x6E1..0x6EC`, `0x6EE..0x705`,
   `0x707..0x708`, `0x70A`, `0x70C..0xCFF`, **and each plus `0x20000`**.
4. `0x1B00..0x1B1E`, `0x21B00..0x21B1E`.
5. `0x7000`, `0x7004`, `0x7007`, `0x701A`, `0x7020..0x7023`,
   `0x702E..0x702F`.

No other Flash value changes. Generic marker at `0x180` is unchanged.

## Optional complete BBB comparison

This was materially useful to distinguish signature-dependent portions of
the **complete** operation, not to repeat Task D's first-page proof.
Restored the already available BBB pre-confirmation checkpoint into
`local/task-e/bbb-001/`; pressed Select once and used identical capture and
quiet budgets. Birthday/result/other inputs stayed unchanged. Both routes
reach Brain Age 35. All eight API boundary system-cycle timestamps match.

Completed AAA HA versus BBB HB differs in **550 bytes**, exactly **275 in
each 1792-byte copy**. Only API payloads 1 and 2 differ; all six subsequent
payloads are byte-identical in this control.

Exact differing ranges in the lower copy:
`0x610`, `0x61B..0x640`, `0x643..0x651`, `0x653..0x696`,
`0x698..0x6C2`, `0x6C4..0x6EC`, `0x6EE..0x706`, `0x708..0x713`,
`0x715..0x724`, `0x726..0x727`, `0x729..0x72A`, `0x72C..0x734`,
`0xCFC`, `0xCFE..0xCFF`; **the same 14 ranges plus `0x20000`** form the
upper copy. No signature algorithm or checksum was decoded. The narrow
conclusion is input dependency of the two complete copies, not universal
independence of every other profile field or save operation.

## Restart and actual profile recognition

Preserved exact completed live Flash snapshots before termination. The
baseline's savestate import deliberately detaches automatic battery
write-through; the restored source session's original disk save therefore
remains H0. No persistence flag or save semantics was changed. Used the
legitimate completed `cart_save` snapshot as an ordinary durable save file
for a **fresh runner**, with no savestate import and no profile recreation.

Terminated the paused original runner after full capture and the quiet
interval, then launched `local/task-e/restart-001/`. Immediate full-image
reload hash is **HA**, exactly matching the completed snapshot, with both
guest instruction counts still zero. A bounded passive startup of
730000000 ARM9 cycles reached the title/menu. Then one Daily Training menu
tap `(144,96)` and a 300000000-cycle observation exposed the existing-profile
selection screen. This tap belongs only to the separate recognition check,
not to the original confirmation sequence.

**Recognition evidence:** first data-file button visibly contains the exact
handwritten **AAA** signature and **Brain Age: 35**. Three other buttons say
New Data File. Left screen says "This training will help your basic
brainpower." Stopped there: no profile selected, no More, no exercise.

Immediately loaded, passive-startup and recognition snapshots are all HA.
Across both startup and recognition: **zero logical write APIs, zero page
submissions, zero Flash commits, zero changed bytes**. The normal on-disk
save in the new runner also remains HA. Exact final image is preserved.

The headless serve build has no graceful frontend-exit facility
(`nds_frontend_request_exit` returns false without SDL). Only verified Task E
PIDs were terminated while paused, after complete snapshot preservation.
No in-flight save operation was truncated. All Task E runners are stopped.
Automatic write-through from a restored state is not claimed; durable
snapshot-file reload **and guest recognition after a real boot** are proven.

## Proven, supported, inferred

- **PROVEN:** complete seven-page primary write, its seven-page mirror,
  six additional small/block operations, exact net/touched ranges, full
  byte-exact replay, stable quiet UI, durable exact reload, and actual AAA / 35
  recognition after startup without recreation or further writes.
- **SUPPORTED:** confirmation commits the tested Calculations-route profile
  through a replicated signature-dependent structure plus accompanying
  records. User-specific data proof from Task D remains established.
- **INFERENCE/unmapped:** precise compression/signature format, checksums,
  index flags, every other profile field, and future save ordering.
  No voice/Stroop equivalence, exercise, RTC/day progression or Task F claim.

## ROM-free changes, validation and reproduction

New files only:

- `tools/task_e/capture.py`: bounded tap/wait capture, full old-byte replay,
  local frames/snapshots/state, one tap permitted per isolated session.
- `tools/task_e/launch_saved.py`: fresh launch of the observed completed
  save, SHA-1 gate, full immediate reload verification; no savestate import.
- `tools/task_e/analyze_save.py`: checks every API's complete source/page
  slicing, FIFO/worker identity, physical transaction, old bytes, full final
  image, paired copies, optional whole-save differential and restart images.
- This report.

No runtime, Flash semantics, Brain Age bytes, generated C or existing Task D
stop guard was changed. Python compilation, exact full-sequence auditor,
restart/disk-image checks and `git diff --check` passed. Raw traces, images,
saves and states stay ignored locally; none is committed or uploaded.

The normal sandbox execution check failed before command execution with
`helper_unknown_error: setup refresh had errors`. Supported per-operation
`require_escalated` execution then worked under auto-review, without Graham
approval spam, human escalation or approval-capacity failure. No full access,
approval-policy weakening or approval-infrastructure change was made.
The bundled apply_patch helper handled the existing reparse-point issue.

Representative commands from the existing checkout, each using the normal
supported approval path where execution requires escalation:

```powershell
python tools/task_c/restore.py --source local/task-d/route-001/13-confirm-profile-review --out local/task-e/aaa-001 --port 19855
python tools/task_c/step.py --out local/task-e/aaa-001 --label 00-baseline --baseline --cycles 0 --savestate
python tools/task_e/capture.py --out local/task-e/aaa-001 --label 01-confirm-once --tap 240 152 --cycles 300000000 --savestate
python tools/task_e/capture.py --out local/task-e/aaa-001 --label 02-quiet-settle --cycles 200000000 --savestate
python tools/task_e/launch_saved.py --source local/task-e/aaa-001/02-quiet-settle --out local/task-e/restart-001 --port 19857
python tools/task_e/capture.py --out local/task-e/restart-001 --label 00-reloaded --cycles 0
python tools/task_e/capture.py --out local/task-e/restart-001 --label 01-passive-startup --cycles 730000000 --savestate
python tools/task_e/capture.py --out local/task-e/restart-001 --label 02-recognize-profile --tap 144 96 --cycles 300000000 --savestate
python tools/task_e/analyze_save.py --aaa local/task-e/aaa-001 --bbb local/task-e/bbb-001 --restart local/task-e/restart-001 --output local/task-e/complete-save-audit.json
```

BBB uses `local/task-d/differential-001/13-confirm-profile-review` with port
19856 and identical confirmation/quiet budgets. Existing directories must
not be overwritten. Terminate only the corresponding verified runner PID
after capture, before the fresh restart; do not execute all commands against
still-running old sessions without that boundary.

Ignored evidence paths: `local/task-e/{aaa-001,bbb-001,restart-001}/` and
`local/task-e/complete-save-audit.json`. Each capture folder contains full
before/after saves, book/raw frames, logical/physical logs, debug responses,
summary and optional checkpoint. Final AAA snapshot:
`local/task-e/aaa-001/02-quiet-settle/after.sav`; durable restart save:
`local/task-e/restart-001/erased.sav` (conventional filename, **not erased**).

**Stop after Task E. No Task F.**
