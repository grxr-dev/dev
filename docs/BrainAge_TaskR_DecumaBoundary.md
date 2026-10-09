# Task R: original handwriting input and recognition boundary

2026-10-09. **PASS for the bounded input/result boundary.** One original
Calculations x20 answer, two-stroke **4** for **11 - 7**, was accepted. No Task Q
strokes were submitted, no adapter implemented, and no Task S work begun.
All semantic labels below are analyst-assigned; no Decuma API symbol names are claimed.

## Recovery and authority

Started clean on codex/brainage at Task Q
`ee50d1587092d908e94446510f3fd9c07fa29b45`. Read Tasks Q and P first.
Tasks C/G document accepted numeric handwriting through ordinary guest touch.
`tools/task_c/digits.py` defines the proven pen paths; Task G's capture helper
records 2,000,000 ARM9 cycles per supplied position and 3,000,000 per pen-up.
Task G preserves a checkpoint after each answer. Task I identifies calculation
update 0x02026710 and constructor 0x02027A28, but contains no recognition trace.
Stage 0 identifies the Decuma database. No prior stroke-memory/call-boundary
trace was found in the reviewed reports/helpers, so one instrumented answer was needed.

Reused `local/task-g/session-001/11-answer-01-63/checkpoint.state` and its
`after.sav`. Its screenshots show the prior accepted 9 x 7 = 63, current
11 - 7, and next 3 + 7. The preserved `12-answer-02-4/summary.json` contains
exactly the reused two-stroke path. No new glyph, menu route, or onboarding.
The loaded checkpoint already has one historical answer; this task adds only one.

Authoritative new session: `local/task-r/answer-002/`. `answer-001` stopped at
a tuple/list preflight assertion after restore and read-only captures, before
any run_cycles or touch request. It is preserved. The corrected driver normalizes
its path to JSON lists. No failed drawing, answer retry or state rollback occurred.

ROM SHA-1 checked at launch: b8a105bacc3234dede8d4465df0869f2b922a0e2.
Framework remains 3a57236bb23d25dcb4caad7d58d733311062ff5e plus existing
project facilities and the new read-only observer. Separate headless build:
`build/task-r-runner/nds_runner.exe`; existing headless/SDL runners were not rebuilt.
Task R executable SHA-256:
`9c0ee1c7b1a39b6e8e006398aa8ac86c1408bb638585849588be21f0ee8776c1`.
Existing headless and SDL executable hashes were rechecked against Tasks P/Q:
`19ddb95320ccca985b42ead833c5add233a3d315222dff962c21fae1e022d76c` and
`c47e21fd4e503eaac73700cba8b480a8e5285a077be1c9af59ec7cc8b91331ce`.

The actual answer uses --force-tier3, original guest input/logic and existing
public FreeBIOS/direct boot configuration. This proves execution in the project's
native runner with interpreter fallback, not compiled execution of every instruction.

## Middleware identity and narrow static map

ARM9 string `/data/Decuma/_databas_le.bin` is at guest 0x020CC598,
ROM 0x000D0598, referenced by pointer word 0x0205335C. Setup routine
0x020531C8 loads it through 0x02066124 and stores the resource pointer in
manager+8. Setup allocates per-slot contexts using the size helper 0x020A3F08,
and puts the database pointer into the 16-byte configuration at slot+0x20.
Slot activation calls 0x020A447C at 0x020523E8 with that configuration.
The same slot's context is passed to recognition 0x020A41A0.
This resource/configuration chain strongly supports Decuma ownership of the
boundary; it does not assign every neighboring function to that library.
Initialization happened before the restored checkpoint, so this linkage is
**strongly supported statically**, not newly traced initialization.

| Role | ARM9 address | Evidence |
|---|---|---|
| Calculation update | 0x02026710 -> 0x02026510 | Static; 0x02026510 dynamically observed |
| Original handwriting update/accumulator | 0x02052424, called at 0x0202668C | Dynamic arguments and samples; static caller |
| Point stores | 0x02052534 / 0x02052544 | Dynamic before/after snapshots plus static instructions |
| Pen-up descriptor finalization | 0x02052590..0x020525F0 | Dynamic counts, pointer, prior contact and pen-up |
| Submit worker item | 0x0205204C; call at 0x020525E4 | Dynamic; queue send 0x020520B0 |
| Recognition worker | 0x02051A30 | Dynamic body; static thread entry setup |
| Immediate recognition call | 0x02051AF4 -> 0x020A41A0 | Dynamic, return 0x02051AF8 |
| Candidate/metadata accessors | 0x020A3FB8, 0x020A3FFC, 0x020A3F2C | Dynamic calls and outputs, static callsites |
| Worker result publication | 0x02052034 | Before/after completion-byte snapshots |
| Candidate-to-number consumer | 0x02052424, conversion 0x020527FC / 0x0205291C..2C | Dynamic result and static conversion |
| Exercise submission | 0x020266B4 -> 0x02025778 | Dynamic arguments (exercise,0,4) |
| Correctness validation | 0x02025698; compare 0x02025728 | Dynamic 4==4 and success stores |
| Accepted-answer phase transition | 0x020265F8 | Dynamic correct count and subsequent phase readback |

Only these wrappers, input preparation and immediate public-facing callees were
inspected. No broad Decuma decompilation, unrelated services or coverage expansion.

## Original stylus representation

Input uses the established headless debug `touch` command through ordinary guest
ADC/input delivery, not SDL events, custom-host touch ownership, direct recognition
calls, or guessed buffer writes. The driver supplies these raw DS coordinates:

- Stroke 0: (190,110), (156,91), (121,65), (121,98), (121,130), then pen-up.
- Stroke 1: (173,114), (132,114), (75,114), then pen-up.

At point storage, guest touch structure 0x020DA4E4 contains 16-bit x at +0,
y at +2, contact=1 at +4; +6 is observed zero, with broader meaning unassigned.
Every point snapshot is checked against the most recent driver touch event.

Objects in this run (addresses are observations, not stable allocation contracts):

| Object | Address / fields |
|---|---|
| Calculation object | 0x020E9A00 |
| Handwriting manager | 0x020FA808; +0 slot count=1, +4 slot-array pointer, +0xC active slot index, +0x234 prior-contact byte |
| Handwriting slot, stride 0x370 | 0x020FAA50 |
| Slot raw input rectangle | +0xC/+0x10/+0x14/+0x18 = 54,6,247,183 |
| Point array | slot+0x208 -> 0x02125CF4 |
| Descriptor array | slot+0x20C -> 0x020FC0D0 |
| Current stroke's start index | slot+0x210; becomes cumulative end on pen-up |
| Total recorded points | slot+0x214, 32-bit |
| Finalized stroke count | slot+0x218, 32-bit |
| Persistent recognizer context | slot+0x1C -> 0x0211B994 |

On initial contact the accumulator finds an enabled rectangle and selects its
slot. Subsequent held contact appends once per update, including identical
positions. It clamps to the rectangle, then stores **(raw_y, 255-raw_x)**.
This is book-oriented pixel space, with no scale factor or origin subtraction
at the title's storage boundary. STRH writes two little-endian 16-bit fields,
stride **4**. Signed coordinate loads are supported statically by the downstream
input conversion; this run only tests positive values. No timestamp, pressure,
contact bit or pen-up sentinel occurs in a point element.

Pen-up is a state transition: prior-contact byte nonzero, current touch contact
zero. The accumulator writes an **8-byte descriptor**: 32-bit point count at +0,
32-bit pointer to the first point at +4. It queues recognition, increments the
stroke count, resets active slot to -1, and later clears prior-contact. The next
stroke starts at the previous cumulative endpoint in the same flat point array.

Final captured points (repeats deliberately retained):

```text
stroke 0, 9 points:
(110,65) (110,65) (91,99) (91,99) (65,134)
(98,134) (98,134) (130,134) (130,134)
stroke 1, 5 points:
(114,82) (114,123) (114,123) (114,180) (114,180)
```

Descriptors are `(9,0x02125CF4)` and `(5,0x02125D18)`; total **14 points**.
The eight supplied positions produce fourteen sampled points because each is
held for guest time. Task Q deduplicates input updates; equivalent sampling or
recognition quality cannot be assumed.

Static allocation/bounds: point storage 0x4000 bytes / 4096 point slots;
descriptor storage 0x100 bytes / 32 descriptors. The accumulator checks these
limits, and the manager queue holds 16 records. No limit was exercised; middleware
maximums and full-buffer policy are not established by this run.

## Queue and recognition invocation

The UI submits through 0x0205204C. Each 20-byte manager queue record carries
slot pointer +0, slot-generation value +4, stroke index +8, cumulative stroke
count +0xC and completion byte +0x10. The new records here are at
0x020FA918 and 0x020FA92C, generation 5, indexes 0/1, counts 1/2. Older
records in the restored manager must not be mistaken for this answer's requests.
The worker checks the generation, then uses slot+0x20C + index*8.

Recognition is **asynchronous relative to the UI**, through a guest worker queue;
**synchronous inside that ARM9 worker**. No ARM7 recognition request is involved
in the observed chain. 0x02051AF4 calls 0x020A41A0 once for each newly finalized
stroke, retaining the same context across both. This is incremental submission,
not a single call receiving the full two-stroke aggregate.

| Argument | Observed meaning/value |
|---|---|
| r0 | Context 0x0211B994 |
| r1 | Current descriptor 0x020FC0D0, then 0x020FC0D8 |
| r2 | Stroke identifier 0, then 1 |
| r3 | Group-0 16-bit output buffer, slot+0xE4 = 0x020FAB34 |
| stack+0 | Group-0 capacity 16 |
| stack+4 | Group-0 count output 0x02131BF8 |
| stack+8 | Group-1 output buffer, slot+0x104 = 0x020FAB54 |
| stack+12 | Group-1 capacity 16 |
| stack+16 | Group-1 count output 0x02131BFC |
| LR / return site | 0x02051AF8 |
| Return value | r0=0 on both calls |

The descriptor and raw point array are passed directly; no separate title-side
normalized-point copy precedes this call. The boundary's internal path reads
count/pointer and invokes conversion via 0x020A4718 / 0x020B387C. Internal
resampling/normalization is intentionally not mapped and is not a Task Q adapter
requirement inferred from this experiment.

## Results versus correctness

Both calls produce group counts **0 and 1**. Group 0 begins with a zero
terminator. Group 1 contains **0x0032,0** after stroke 0, then **0x0034,0**
after stroke 1. These are 16-bit ASCII-compatible digit codes; general Unicode
or alternate symbol encoding is unproven. This establishes one selected/current
character in group 1, not a count of all internal alternative hypotheses.

The worker calls these immediate accessors for group=1, index=0:

- 0x02051BE0 -> 0x020A3FB8, writes a 32-bit metric to slot+0x144:
  **500**, then **249**. Its meaning/calibration is unknown; not claimed confidence.
- 0x02051C04 -> 0x020A3FFC, writes additional character data at slot+0x124;
  observed first code 0x0030. Its role is not the selected answer.
- 0x02051C1C -> 0x020A3F2C, returns contributing-input metadata and writes
  count **1**, then **2** at slot+0x184. Static code links these identifiers
  to stroke identifiers; unrelated metadata fields remain unmapped.

The worker sets queue completion at 0x02052034. UI consumption at 0x0205274C
occurs later. In this run, group 0 is empty, so the group-1 loop subtracts 0x30
and accumulates decimal digits, storing **2**, then **4**, at slot+0x320.
The title also contains expected-answer-dependent gating/delay logic using
slot+0x224 and +0x31C; do not transplant this policy as Decuma recognition.
The incomplete first-stroke value 2 is not submitted as an exercise answer.

Only once, at 0x020266B4, the game calls 0x02025778 with
(exercise=0x020E9A00, slot=0, value=4). It writes exercise+0x514=4 and calls
0x02025698. At 0x02025728, recognized unit **4** is compared with expected
unit **4** from exercise+0x4C. Equality sets +0x20=1 and +0x504=1; the next
success path increments correct-answer count +0x44 from 1 to 2 and sets phase
+0x10 to 2 at 0x020265F8. Final readback proves phase 2 and correct count 2.
The exercise is not complete (configured total 20). The final screenshot still
shows the drawn 4; stopping precedes its next feedback rendering. Acceptance is
proved by the value/comparison/state chain, not an invented screenshot checkmark.

## Timeline and independent validation

All times below are ARM9 guest cycles, not host time:

| Event | Cycle |
|---|---:|
| Restored ready checkpoint | 3416309760 |
| First stored point | 3416894042 |
| Stroke 0 finalization | 3426960437 |
| Recognition call / return, stroke 0 | 3427094697 / 3428653845 |
| Numeric result 2 | 3429199575 |
| Stroke 1 finalization | 3435925564 |
| Recognition call / return, stroke 1 | 3436059997 / 3440013393 |
| Numeric result 4 | 3440403311 |
| Exercise submission | 3440403480 |
| Correctness comparison / success flags | 3440403563 / 3440403573 |
| Accepted phase transition | 3441640474 |

`BrainAge_TaskR_Timeline.json` is a compact, ROM-free 39-event timeline of all
ten touch events, fourteen stored points, finalizations, calls/results and
acceptance. Local `timeline.json` preserves the same derived data.
`tools/task_r/analyze.py` independently checks all point stores against source
inputs and after-store bytes; descriptors/counts; call registers/stack; return
codes/terminators/counts; worker publication; decimal result; correctness flags;
accepted phase/correct count; and unchanged full Flash.

Observer capture: 182 snapshots, 799888 bytes, below its 12000-record cap.
SHA-256: 3c22f8a6b8737961c533c751acad5c54f941e26a237fe2b86220157508714536.
Raw snapshots and finalized-point/descriptor hex remain local/ignored.

## Save safety and execution scope

Disposable before, live-after export, and on-disk Flash are byte-identical,
262144 bytes, SHA-256:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
Logical save requests **0**, Flash commits **0**, changed bytes **0**.
The driver checks A/C traces after every execution quantum and would stop on
any event. It validates live Flash independently; it does not infer safety from
the imported state's detached disk write-through. Source save and savestate
are rechecked unchanged. Canonical Task G/H0 and Task Q artifacts are untouched.

The owned diagnostic process was terminated after read-only final captures;
no Back/completion/results/stamp transition was attempted. This adds one accepted
answer only, no completion save or progression-policy changes. Custom activation
selectors were removed from the subprocess environment. bc_host.h, bc_freehand.h
and bc_quiz.h are unchanged; no custom-host regression run was needed.

## Minimum future adapter contract (design only)

`BrainAge_TaskR_Contract.json` records the proven fields and explicit unknowns.
A future bounded experiment needs guest-addressable little-endian point pairs,
8-byte count/pointer descriptors, ordered stroke identifiers, and a live correctly
initialized title recognizer context retained across strokes. For raw DS
coordinates use (raw_y,255-raw_x), respecting the original input rectangle.
Task Q's landscape canvas has a different UI layout; a deliberate canvas-to-book
mapping remains a future design choice. Do not claim its deduplicated points are
already compatible or invent pen-up sentinels.

Use the observed 0x020A41A0 boundary and two output groups/count pointers, retaining
all input/output memory through queued worker completion. Read group-1 16-bit
digit data for this demonstrated route, separate from the exercise's expected
answer and delay/correctness policy. Original lifecycle resets context via
0x020A437C; standalone context creation, exact context size and general output
semantics are not established. Original allocations' limits are static bounds,
not tested middleware guarantees. Metric meaning and internal normalization remain
unknown. No arbitrary letters, symbol sets, standalone middleware reuse or
production recognition claim follows.

Recommended Task S only: in an isolated checkpoint, reuse an already initialized
original context and test one known two-stroke 4 through a bounded Task Q-to-input
adapter, comparing its result with this original-path baseline. Establish the
coordinate mapping and lifetime first; exclude gameplay correctness/save/menu
integration. **Not implemented or begun here.**

## Tools and reproduction

Normal sandbox process creation failed with `helper_unknown_error: setup refresh
had errors`. Explicit require_escalated execution passed auto-review. No human
approval was requested in Task R, and no policy/network/relay settings changed.

ROM-free tools: request_trace.h (selected pre-instruction RAM snapshots),
install.py (one opt-in interpreter observer), run_answer.py (isolated one-answer
driver), analyze.py (decoder/audit), static_map.py (bounded local disassembly).
The observer reads only RAM, writes diagnostic files, and changes no guest
register, bus store or timing accounting. Historical A/C trace hooks are reused.
It is a pinned-checkout diagnostic, not a portable middleware integration.

With the existing local toolchain and Task Q checkout:

```powershell
python tools/task_r/install.py
$env:PATH = "$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake -S local/ndsrecomp/runner -B build/task-r-runner -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DNDS_SDL_BACKEND=NONE -DNDS_ENABLE_COMPUTE_RENDERER=OFF -DNDS_BOOTSTRAP_FIRMWARE=ON "-DNDS_RECOMP_UI_ROOT=$PWD/local/recomp-ui" "-DNDS_GENERATED_DIR=$PWD/generated/public" "-DNDS_TITLE_BANK_DIR=$PWD/generated/brainage" -DNDS_TITLE_ROM_SHA1=b8a105bacc3234dede8d4465df0869f2b922a0e2
cmake --build build/task-r-runner --target nds_runner --parallel 4
python tools/task_r/run_answer.py --out local/task-r/NEW
python tools/task_r/analyze.py --out local/task-r/NEW
python tools/task_r/static_map.py --rom '../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' --out local/task-r/static-NEW
```

The driver requires the preserved Task G source and rejects reused output
folders. No generated C is manually edited. Only ROM-free scripts, the mapping
report and compact derived JSON are versioned; saves, checkpoints, binaries,
images, raw dumps and ROM-derived disassembly remain ignored.
