# Brain Age Task G: one Daily Training exercise and persistence

Date: 2026-10-09. **One Calculations x20 session completed through its earned
January-2 stamp. Complete save sequence and exact clean reload are proven.
Restart's independent visible calendar/result recognition is incomplete:
a mandatory picture-drawing introduction precedes the calendar, and no
second activity was started.**

## Recovery, route and unchanged runtime

Used the existing `dev` checkout on `codex/brainage`, starting at Task F
`c3957caa182e1bf096cf1179f7e66077694e6c44`. Framework remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`. Reused the existing
`build/task-a-runner/nds_runner.exe`, Task A/C causal observers, direct boot,
FreeBIOS, generated firmware, config, headless serving and forced Tier-3.
No rebuild, ROM/generated-C edit, save-semantic change or coverage work.

Restored `local/task-f/next-day-001/04-quiet-settle/checkpoint.state` into
new `local/task-g/session-001/`; Task F evidence is untouched. State SHA-256:
`15ace8ad92fde4a0dd4ad1e86ce7c88cff671fa0604998351791ad0c5cc8d94f`.
CPU controls, cycles and instruction ordinals exactly match the source:
ARM9 cycles 1530394624, instructions 142931200; ARM7/system cycles
765197312, instructions 49777636. Full live Flash and RTC also match.
Initial UI: AAA returning-profile **Hello!**, More enabled. Guest RTC:
**2024-01-02 12:00:22**. `CLEAR-RAM-CHECK` remains at `0x180`.
The restore and fresh-launch helpers independently verify ROM SHA-1
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

The known Task F 48-byte return operation is already complete and is not
counted again. New logical/Flash traces start at zero. All new phase
captures record full before/after saves, hashes, CPU/timing/RTC, screenshots,
logical/physical events, independent old-byte replay and checkpoints.
Imported states detach normal automatic battery write-through; the legitimate
completed live Flash export is used for the subsequent ordinary fresh boot.
No persistence flag or save behavior is changed.

Full 262144-byte Flash identities:

- **H0**, January-2 post-return / pre-exercise:
  `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
- **H1**, settled automatic calculation result:
  `24ebf5db950d664d6df08576fc80a113c8adeb69a1aa402419d64f3e802b9c67`.
- **H2**, after rank Next / before stamp:
  `c1aa4b2bee400210fe89df0062fae13c8e846e00f0e65078108abdae07b34f00`.
- **H3**, fully completed exercise and earned stamp:
  `2531e8a54ab0ceabc65f23035c8c02064d5a7c4c9cc2042c38e1eed0aace3ed1`.
- **HR**, after separate fresh-restart profile entry:
  `2eab9dd70f7cf659fcc90a134931a4cb466628f04de70653c0fae7434065fcfa`.

## Pre-exercise and exercise entry

Chosen **Calculations x20**: normally available, deterministic nonvoice input,
existing Decuma pen paths. No availability manipulation, unlock or second
exercise. The original Training menu already contains Calculations x100
and Reading Aloud; later x100 advice is not proof of a new unlock.

Every following transition was separately captured, with **zero logical
write APIs, zero Flash commits, zero changed bytes**, before/after H0:

| Capture | Normal action / resulting state |
| --- | --- |
| 00-restored | No input; restored Hello greeting |
| 01-hello-more | More; cold-weather greeting |
| 02-greeting-more | More; returning-profile greeting, Next enabled |
| 03-return-next | Next; AAA January calendar / Daily Training home |
| 04-training-menu | Training; normal exercise-selection menu |
| 05-select-calculations-x20 | Calculations x20; required rule introduction |
| 06-rules-more | More; handwriting/speed instruction |
| 07-rules-write-more | More; benefit explanation |
| 08-rules-benefit-more | More; readiness dialogue |
| 09-rules-next | Next; normal press-to-start button |
| 10-start | Start; first actual problem |

Raw taps: More/Next `(240,152)`, Training `(137,96)`, Calculations x20
`(166,75)`, Start `(117,96)`. No rules skipped. Pre-exercise menu checkpoint
04: system cycle 1140212430; API count 0; commit count 0; H0.

## Answers: one session, normal touch only

Twenty required problems were ultimately accepted correctly. **Twenty-two
handwriting submissions** and **one normal Erase tap** were used, not twenty
perfect first-attempt submissions. Two visual reading mistakes were preserved:
problem 11 first received 0, then 1; problem 15 first received 7, then Erase
and 35. The game did not advance on those initial inputs. The visible final
result reports **Missed 0, Penalty 0 seconds**; no unsupported explanation of
recognizer timing/penalty rules is claimed. No rollback hides the attempts.

| Accepted index | Problem | Accepted answer |
| --- | --- | ---: |
| 1 | 9 x 7 | 63 |
| 2 | 11 - 7 | 4 |
| 3 | 3 + 7 | 10 |
| 4 | 9 + 4 | 13 |
| 5 | 12 - 7 | 5 |
| 6 | 9 - 5 | 4 |
| 7 | 5 x 4 | 20 |
| 8 | 11 - 7 | 4 |
| 9 | 0 x 5 | 0 |
| 10 | 0 + 6 | 6 |
| 11 | 7 - 6 | 1 |
| 12 | 3 x 0 | 0 |
| 13 | 2 + 4 | 6 |
| 14 | 9 + 5 | 14 |
| 15 | 7 x 5 | 35 |
| 16 | 7 + 1 | 8 |
| 17 | 6 x 1 | 6 |
| 18 | 2 + 2 | 4 |
| 19 | 8 - 6 | 2 |
| 20 | 11 - 7 | 4 |

Pen paths reuse `tools/task_c/digits.py`: actual touch coordinates, 2000000
ARM9 cycles per point and 3000000 pen-up cycles per stroke. Each problem's
screen is inspected before the next answer. No score, answer, RAM or save
injection. Captures 11..32, including both correction sequences, all remain
H0 with **zero requests/commits**. All accepted-answer indices and every
attempt's deterministic start/end system cycle are retained in the local
phase audit. Closest pre-final checkpoint: `32-answer-19-2`, final problem
11 - 7 visible, system cycle **2388158464**, API/commit counts both zero.

## First persistence and separate completion transitions

**First persistent completion transition: handwrite final answer 4, then
allow the automatic result transition.** The first enclosing API appears at
system cycle **2487633676**, instruction **378678941**, before any results
Next/More action. First Flash byte commits at **2487636511**.

Capture 33's bounded observation happens to end during the multi-page save:
it contains the first 256-byte page, 4 value changes and transient blank
screens. This is **not** a completed enclosing operation or durable result
claim. Continued immediately with no input in capture 34, completing the
remaining page and companion writes. Stable result: **22 seconds**, New
Record, zero penalty; individual/all top-three result shows #1 at 22 seconds.

| Boundary | Action / result | APIs | Commits | Changed-byte commits | Result hash |
| --- | --- | ---: | ---: | ---: | --- |
| 33 + 34 | Final answer + automatic result settling | 4 | 540 | 84 | H1 |
| 35-results-next | Next; car-speed rank | 0 | 0 | 0 | H1 |
| 36-rank-next | Next; dated graph and exercise feedback | 1 | 48 | 15 | H2 |
| 37..48 | Each required More measured separately; performance/brain/training-tip dialogue, finally stamp invitation | 0 | 0 | 0 | H2 |
| 49-stamp-next | Next; prompt to touch today's date | 0 | 0 | 0 | H2 |
| 50-stamp-today | Tap January 2 `(97,96)`; earned-stamp confirmation | 3 | 112 | 27 | H3 |
| 51-completed-quiet | No input, quiet interval | 0 | 0 | 0 | H3 |

No More pressed after the stable earned-stamp confirmation. No second
exercise selected. This separates automatic score persistence, rank/graph
continuation bookkeeping, and actual user-driven calendar stamping.

## Complete enclosing save operations

All entries are real ARM9 ARM-mode Tier-3 API observations at `0x0200DE78`.
Immediate callsites are captured LR minus four, not fabricated symbols.
No new giant caller trace. Page lengths and source identity are independently
checked against actual API payloads and all downstream stages.

| Op / boundary | Callsite | Flash target | Length | Source | API system cycle | Instruction | Segmentation | Writing transactions | Changed commits |
| --- | --- | --- | ---: | --- | ---: | ---: | --- | --- | ---: |
| 1 / final answer | `0x0202DD88` | `0x400` | 428 | `0x020E9818` | 2487633676 | 378678941 | 256+172 | 5,11 | 8 |
| 2 / final answer | `0x0202E018` | `0x1b20` | 32 | `0x020E95B8` | 2489438206 | 378684269 | 32 | 19 | 31 |
| 3 / final answer | `0x0202E038` | `0x21b20` | 32 | `0x020E95B8` | 2490293330 | 378685723 | 32 | 25 | 31 |
| 4 / final answer | `0x0202D744` | `0x7080` | 48 | `0x020E95FC` | 2491151888 | 378689035 | 48 | 33 | 14 |
| 5 / rank Next | `0x0202D744` | `0x70c0` | 48 | `0x020E95FC` | 2798601546 | 405869177 | 48 | 41 | 15 |
| 6 / stamp date | `0x0202E018` | `0x1b20` | 32 | `0x020E95B8` | 4589500580 | 648197915 | 32 | 49 | 5 |
| 7 / stamp date | `0x0202E038` | `0x21b20` | 32 | `0x020E95B8` | 4590356142 | 648199369 | 32 | 55 | 5 |
| 8 / stamp date | `0x0202D744` | `0x7100` | 48 | `0x020E95FC` | 4591223766 | 648202793 | 48 | 63 | 17 |

Every transport stages at `0x020D4F60`, shared request `0x020D4CE0`; its
payload pointer, target and length fields match the enclosing source slice.
Submit ARM9 PC `0x0200E080`; FIFO send `0x020091B0`; FIFO receive ARM7
`0x037FE230`; worker ARM7 `0x03802F48`. Every FIFO word is `0x1EB`.
The auditor verifies the payload through all four logical stages, then
against the complete physical transaction, including the final-byte flag.

| Page target / length | Submit | FIFO send | FIFO receive | ARM7 worker | Physical byte sequences | Commit cycles first..last |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `0x400` / 256 | 2487634194 | 2487634280 | 2487634434 | 2487634999 | 1..256 | 2487636511..2487667300 |
| `0x500` / 172 | 2488544392 | 2488544478 | 2488544644 | 2488545209 | 257..428 | 2488546721..2488567242 |
| `0x1b20` / 32 | 2489438373 | 2489438459 | 2489438597 | 2489439162 | 429..460 | 2489440674..2489444395 |
| `0x21b20` / 32 | 2490293498 | 2490293584 | 2490293763 | 2490294328 | 461..492 | 2490295840..2490299561 |
| `0x7080` / 48 | 2491152084 | 2491152170 | 2491152343 | 2491152908 | 493..540 | 2491154420..2491160061 |
| `0x70c0` / 48 | 2798601742 | 2798601828 | 2798601981 | 2798602546 | 541..588 | 2798604058..2798609699 |
| `0x1b20` / 32 | 4589500747 | 4589500833 | 4589500996 | 4589501561 | 589..620 | 4589503073..4589506794 |
| `0x21b20` / 32 | 4590356310 | 4590356396 | 4590356579 | 4590357144 | 621..652 | 4590358656..4590362377 |
| `0x7100` / 48 | 4591223962 | 4591224048 | 4591224194 | 4591224759 | 653..700 | 4591226271..4591231912 |

Physical command is consistently `0x0A`, host commit `flash_spi_write`.
Both **carried command origin and individual byte origin** are ARM7 ARM
PC **`0x038032B8`**, Tier-3; not a late sample of whichever CPU happens to run.
Old/new bytes, SPI positions and instruction ordinals remain in ignored logs.
Representative exact values:

- First commit seq 1, tx 5, SPI position 4, last false, offset `0x400`,
  `00 -> 02`. Command origin cycle 2487635986 / instruction 121542446;
  byte origin cycle 2487636511 / instruction 121542710.
- Final commit seq 700, tx 63, SPI position 51, last true, offset `0x712F`,
  `00 -> FE`. Command origin cycle 4591225746 / instruction 218842631;
  byte origin cycle 4591231912 / instruction 218845668.

## Complete Flash diff and narrow structure

H0 -> H3: **8 enclosing APIs, 9 submissions, 9 writing transactions,
700 accepted one-byte commits**, **126 value-changing commit events**, but
**116 net changed bytes**. There are **636 distinct touched addresses**;
64 addresses in the paired 32-byte records are written twice. Thus neither
700 nor 126 is the unique/net changed-byte count. 574 accepted commits leave
their old value unchanged. Transaction IDs include intervening nonwriting
SPI activity; ID 63 does not mean 63 writing transactions.

Complete touched spans, inclusive:
`0x400..0x5AB`, `0x1B20..0x1B3F`, `0x21B20..0x21B3F`,
`0x7080..0x70AF`, `0x70C0..0x70EF`, `0x7100..0x712F`.
The 32-byte lower/upper copies match exactly at separation `0x20000`, both
when first written at result time and when rewritten during stamping.
The 428-byte block is not mirrored by another captured operation. Three
48-byte records use successive targets spaced by `0x40`; exact field names,
record/index roles and checksums are not decoded. The user signature/profile
creation copies at `0x600` and `0x20600` remain untouched.

All 30 contiguous net-changing spans are represented below. The two
32-byte-copy lines also apply at **address + `0x20000`**, adding two spans.
All other listed ranges occur once. Values are focused observed byte diffs,
not semantic field assignments.

| Inclusive range | Before hex | After hex |
| --- | --- | --- |
| `0x400` | `00` | `02` |
| `0x404..0x405` | `0000` | `3305` |
| `0x4dc` | `00` | `23` |
| `0x56c` | `00` | `01` |
| `0x590` | `00` | `01` |
| `0x5aa..0x5ab` | `0000` | `a0ff` |
| `0x1b20..0x1b38 and +0x20000` | `ffffffffffffffffffffffffffffffffffffffffffffffffff` | `340500000000000000000000000000000000000018010201fd` |
| `0x1b3a..0x1b3f and +0x20000` | `ffffffffffff` | `00000000aefd` |
| `0x7080` | `00` | `03` |
| `0x7084` | `00` | `02` |
| `0x7086..0x7087` | `0000` | `0102` |
| `0x709a` | `00` | `ff` |
| `0x70a0..0x70a6` | `00000000000000` | `23180101180102` |
| `0x70ae..0x70af` | `0000` | `a0fe` |
| `0x70c0` | `00` | `04` |
| `0x70c4` | `00` | `02` |
| `0x70c6..0x70c8` | `000000` | `010201` |
| `0x70da` | `00` | `ff` |
| `0x70e0..0x70e6` | `00000000000000` | `23180101180102` |
| `0x70ee..0x70ef` | `0000` | `9efe` |
| `0x7100` | `00` | `05` |
| `0x7104` | `00` | `02` |
| `0x7106..0x7108` | `000000` | `010201` |
| `0x7112` | `00` | `01` |
| `0x7114` | `00` | `01` |
| `0x711a` | `00` | `ff` |
| `0x7120..0x7126` | `00000000000000` | `23180101180102` |
| `0x712e..0x712f` | `0000` | `9bfe` |

Final quiet checkpoint system cycle **4889753568**, RTC January 2 12:02:25.
Last commit **4591231912**; **298521656 quiet system cycles** with no later
save request/commit. All eight API payloads are fully submitted and committed;
full old-byte replay exactly matches the final live 262144-byte Flash.

Visible effects before restart: 22-second New Record / #1, car-speed rank,
January-2 graph point, and explicit earned-stamp confirmation. The initial
calendar had no January-2 stamp. No new-exercise unlock is established:
x100 was already visible. No complete record layout or score encoding study.

## Clean restart: proven storage persistence, visible recognition limitation

Preserved `51-completed-quiet/after.sav` (H3), terminated only the verified
paused Task G runner after all saves/quiet capture, and freshly launched
`local/task-g/restart-001/` with that ordinary save file. No savestate import
or profile recreation. Same deterministic RTC switch
`NDS_TASK_F_RTC_PLUS_ONE_DAY=1`; actual initial guest RTC **2024-01-02
12:00:00**, before any guest instruction. Host clock unchanged.

Immediate reload full hash **H3**, exact byte match. Passive startup and
Daily Training entry also remain H3, with zero requests/commits. Profile
selection visibly recognizes AAA / Brain Age 35. Selecting AAA causes the
separate known transport-style 48-byte return operation:

- ARM9 callsite `0x0202D744`, API `0x0200DE78`, source `0x020E95FC`,
  target **`0x7140`**, length 48; API cycle **535537866**, instruction
  **110441962**.
- Submit **535538062**, send **535538148**, receive **535538308**, worker
  **535538873**; Flash tx **259**, seq **1..48**, commit cycles
  **535540385..535546026**, ARM7 `0x038032B8`, same FIFO/shared/payload checks.
- 48 accepted commits, **18 changed bytes**, ending HR. This write is
  separate from the completed exercise's eight operations. No startup
  writes before profile selection.

All subsequent recorded return dialogue transitions produce zero writes.
The normal on-disk fresh-run save equals HR. The entire exercise block,
stamped mirrored records and three prior 48-byte exercise-associated records
remain unchanged; storage persistence is proven, not merely an in-memory
snapshot remaining available. The appended return record's payload also
retains the previously observed personalized/progression values, without
assigning unsupported field names.

**Visible recognition limitation:** after Hello/cold-weather/repeat-return
Next, the game automatically enters a mandatory picture-drawing introduction,
not the expected home calendar. Capture `06-recognized-calendar` was named
for the intended destination but its actual images show the introduction;
the filename is not evidence of calendar recognition. Capture
`07-return-advice-more` shows instructions to draw a described picture.
No picture was drawn, no second exercise started/completed, and no normal
Back/Skip control is currently visible. Progression stopped there rather
than silently broadening the task. The original completion already visibly
awarded a stamp, but **a post-relaunch visible stamp/exercise marker/retained
22-second result is not independently verified yet**. Changed repeat-return
wording and preserved date/progression bytes are supporting evidence only.

The helper audit proves exact reload and preserved written ranges; it does
not assert unobserved UI recognition. A clarification was requested about
passing instructions solely to look for a normal Back/Skip option. Without
that clarification, no further gameplay is authorized by this report.

## Proven, supported, inference

- **PROVEN:** one normal nonvoice Daily Training session; twenty accepted
  problems, 22 seconds, zero displayed penalty; no entry/mid-answer write;
  first saves after final answer; four complete result operations, one after
  rank Next, three after tapping the stamp date; exact counts/ranges/causal
  correlation; full durable reload and surviving exercise/stamp bytes.
- **SUPPORTED:** the 428-byte block plus replicated 32-byte records carry
  exercise-result/day-progression state, and stamping updates the paired
  records plus a companion 48-byte record. Dynamic boundaries and visible
  result/graph/stamp are the evidence; no speculative field labels.
- **UNRESOLVED:** independent visible completion recognition after restart
  behind the mandatory picture prompt. No second activity was used to force
  this check. Exact field meanings, universal routes or later progression
  behavior remain untested. No voice/Stroop equivalence claimed.

## ROM-free tools, execution and artifacts

Added only:

- `tools/task_g/restore.py`: verifies the Task F snapshot/state/RTC/counters,
  ROM identity and marker before reusing the checkpoint in isolated traces.
- `tools/task_g/capture.py`: bounded single tap/answer/wait captures, reusing
  existing pen paths and physical old-byte replay; no Task C/D guard changed.
- `tools/task_g/analyze_completion.py`: existing API/page/FIFO/worker/Flash
  auditor plus phase counts, RTC checks, focused diff and separate restart
  preservation checks. Raw captures/output remain local.
- `tools/task_g/restart.py`: reproducible fresh-launch wrapper enabling the
  existing Jan-2 RTC switch; no new runtime RTC functionality.
- This report.

Python compilation, complete causal replay/audit, range/disk preservation
checks and `git diff --check` passed. No runtime, generated code, save
semantics, approval infrastructure, host time or profile inputs changed.
No broader validation/performance matrix or other gameplay route.

An initial PowerShell/Python wildcard syntax-check invocation failed because
Python received a literal `*.py`; the explicit four-file invocation then
passed. This did not affect captured runtime results or the auditor.

The routine sandbox execution check returned a tool-output truncation rather
than a usable result; no claim of successful normal execution is made.
Supported individually reviewed `require_escalated` commands then worked
without repeated Graham prompts or human approval. The known sandbox setup
problem remains a tooling caveat, not a fabricated game failure. No full
access, approval-policy weakening or bridge changes. The supported bundled
apply_patch helper handles the existing workspace reparse issue.

Local ignored artifacts:

- `local/task-g/session-001/`: restored run, all semantic checkpoints,
  before/after saves, book/raw frames, trace/debug logs, state snapshots.
- `local/task-g/session-001/32-answer-19-2/`: nearest pre-final checkpoint.
- `local/task-g/session-001/51-completed-quiet/after.sav`: exact completed H3.
- `local/task-g/restart-001/`: fresh-save boot, immediate H3 reload and all
  returning-profile observations; newest recorded checkpoint
  `07-return-advice-more` is the picture-instruction stop point.
- `local/task-g/completion-audit.json`, `task-g-audit.json`: full per-operation
  timing/ordinals/payload identity, all phases and exact changed-byte hex.

Representative commands from the existing checkout:

```powershell
python tools/task_g/restore.py --source local/task-f/next-day-001/04-quiet-settle --out local/task-g/session-001 --port 19855
python tools/task_g/capture.py --out local/task-g/session-001 --label 00-restored --cycles 0 --savestate
python tools/task_g/capture.py --out local/task-g/session-001 --label 04-training-menu --tap 137 96 --cycles 150000000 --savestate
python tools/task_g/capture.py --out local/task-g/session-001 --label 05-select-calculations-x20 --tap 166 75 --cycles 150000000 --savestate
python tools/task_g/capture.py --out local/task-g/session-001 --label 11-answer-01-63 --answer 63 --cycles 85000000 --savestate
python tools/task_g/capture.py --out local/task-g/session-001 --label 33-final-answer-20-4 --answer 4 --cycles 200000000 --savestate
python tools/task_g/capture.py --out local/task-g/session-001 --label 34-automatic-results --cycles 300000000 --savestate
python tools/task_g/capture.py --out local/task-g/session-001 --label 50-stamp-today --tap 97 96 --cycles 400000000 --savestate
python tools/task_g/capture.py --out local/task-g/session-001 --label 51-completed-quiet --cycles 200000000 --savestate
python tools/task_g/restart.py --source local/task-g/session-001/51-completed-quiet --out local/task-g/restart-001 --port 19855
python tools/task_g/analyze_completion.py --session local/task-g/session-001 --restart local/task-g/restart-001 --restart-checkpoint 07-return-advice-more --output local/task-g/task-g-audit.json
```

These are representative phase commands, **not a blind replay batch**. Follow
actual saved screenshots/phase order, never overwrite existing directories,
never reuse a still-running port, and preserve the verified PID termination
boundary before restart. The original execution used the equivalent existing
Task E launcher with the RTC environment set, not an extra replay of the new
wrapper. The headless server lacks a graceful frontend exit; only its verified
paused PID is terminated after capture. Both Task G runners are stopped;
the restart's latest loadable state remains preserved at its instruction
stop point. Nothing raw/ROM-derived is staged.

**STOP AFTER TASK G. No Task H or second exercise.**
