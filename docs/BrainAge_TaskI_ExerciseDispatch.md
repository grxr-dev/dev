# Brain Age Task I: Daily Training dispatch and future hook boundaries

Date: 2026-10-09. **Bounded launch map established for Calculations x20,
Calculations x100 and Reading Aloud. No exercise was answered or completed.**
Architecture is **mixed numeric-table selection and hardcoded scene dispatch**,
not a demonstrated extensible exercise/function-pointer registry. Future hook
work is recommended below, not implemented.

**Scope exception:** selecting Reading's Normal font unexpectedly caused two
16-byte settings writes, changing four bytes in the isolated comparison save.
This is not a save-free comparison and must not be reported as one. The write
was discovered in the final phase audit, after two further non-answer launch
actions; progression was then stopped. No existing evidence or authoritative
save was overwritten. No exercise-result/progression operation was observed.

## Recovery and method

Used existing `dev`, `codex/brainage`, starting at Task H
`6fca3de46c8633b523f9efde18c64ada87a55588`. Framework HEAD remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`, with the existing A/B/C/F diagnostics
and the new opt-in, read-only Task I Tier-3 observer. Rebuilt only `nds_runner`;
no new bank emission, coverage tuning, ROM change or generated-C edit.

Independently verified ROM SHA-1
`b8a105bacc3234dede8d4465df0869f2b922a0e2`. Exact ARM9 bytes at ROM offset
`0x4000`, loaded at `0x02000000`, reconciled with Capstone and generated code.
No Ghidra or matching decompilation.

Restored **the same** Task G `local/task-g/session-001/04-training-menu/`
checkpoint independently into `local/task-i/x20-001/`, `x100-001/` and
`reading-001/`. Source state SHA-256:
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
Source Flash SHA-256, **H0**:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
`CLEAR-RAM-CHECK` at `0x180`. AAA, January-2 Training menu; all three options
normally visible. Initial ARM9 cycles/instructions: 2280424860 / 206817686;
ARM7/system cycles/instructions: 1140212430 / 68005876. CPU controls, both
ordinals, Flash and RTC exactly match the source after every restoration.
Guest RTC: 2024-01-02 12:00:34. G/H evidence remains untouched.

Existing G capture tools provide per-action images, full Flash snapshots,
logical requests, physical commits, independent old-byte replay and savestates.
New observer logs condition-passed ARM9 ARM BL and BX/BLX-register edges with
source PC in `0x02020000..0x0208ffff`; first eight hits per edge, hard 6000-record
cap. Records include sequence, raw instruction, target, registers, system
cycle, ARM9 instruction ordinal and bounded side-effect-free RAM peeks. It
does **not** log every instruction, Thumb, PC-load/computed branches, normal
returns or low-address SDK callers. These omissions are reconciled statically,
not presented as proof that such calls never occur. All three inventories are
below the cap: x20 4227 records / 968 edges; x100 4228 / 969; Reading 4327 / 1014.
System timestamp is ARM9 runtime cycles divided by two, not wall time.

## Identity domains: do not conflate them

All names below are analyst-assigned, not original symbols. High confidence
unless explicitly qualified.

| Domain | x20 | x100 | Reading | Evidence |
| --- | ---: | ---: | ---: | --- |
| Touch-widget index | 5 | 6 | 7 | `0x02076FC8` call arguments |
| Visible menu index | 0 | 1 | 2 | menu object `+0x6c4`, at `0x020EAC60` in these runs |
| Reordered menu entry | 0 | 1 | 2 | `0x020C7880[index]`, first three entries unchanged |
| Launch scene | `0x11` | `0x10` | `0x6e` | `0x020C7814[entry]`, selected global `0x020DA3F0` |
| First-instruction gate bit | 0 | 1 | 4 | `0x020C785C[entry]`, R1 at `0x020773A4` |
| Calculation constructor mode | 1 | 0 | not applicable | R1 at `0x0204E698` |
| Calculation problem count | 20 | 100 | not applicable | live object `+0x3c`, bounded static reconciliation |

These are multiple representations, not one universal exercise enum. The
bit-index domain is identified by `0x0202C668`: it shifts `1 << R1`, tests
halfword `+6` through the profile-related pointer table `0x020D71E8`, and
returns whether that bit is clear. It is **not** an exercise-ID setter. Calling
it an instruction-history gate is supported by the subsequent branch into
rules, but the meaning of every bit is not mapped.

## Common route and provisional function map

```text
scene 3 / Training menu
  frame dispatcher 0204F91C -> callsite 02050020 -> menu update 02076E24
  menu index -> order table 020C7880 -> scene table 020C7814
  selected scene written at 0207737C to 020DA3F0
  gate call 020773A4 -> 0202C668, with parallel bit table 020C785C
  first-use branch chooses rules scene 41 in menu object's +6cc
  fade/transition completes; 02077AB0 publishes desired scene to 020DA3EC
  02050264 -> scene lifecycle setter 0204D790
    old-scene cleanup; publish current scene 020DA464; new-scene initialization
  scene 41: common rules initializer 020610B4 / update 0205CDBC
  normal Start -> scene 43 / common countdown
  countdown -> selected scene 11, 10 or 6e
    11/10: shared calculation constructor 02027A28, graphics/setup 0202756C
    6e: Reading constructor/resource loader 02085BA8, graphics/setup 020857E0
```

`0x0204F91C` is the bounded frame function entry, not the numerous interior
labels named as functions by current generated-code emission. It copies
current scene to desired scene at `0x0204FC74`, runs the appropriate update,
compares desired/current at `0x0205025C`, then calls `0x0204D790` if changed.
`0x020DA464` is current scene; `0x020DA3EC` desired scene;
`0x020DA3F0` selected exercise launch scene. Those roles are established by
stores, reads, branch cases and live values, not names inferred from UI alone.

`0x02076E24` is the shared menu update/input handler. Its own small internal
phase switch uses object `+0x6b4`. Widget actions select menu entry `+0x6c4`;
the selected target is retained in `+0x6cc` while the fade completes. Menu
object in these captures: `0x020EA59C`, obtained through `0x020DA4A0`;
that global becomes null after menu teardown. These heap addresses are
observations, **not stable host ABI constants**.

Tables are nine-word numeric arrays in this menu path:

| Address | Role | First three values |
| --- | --- | --- |
| `0x020C7880` | visible-index/order remap | 0, 1, 2 |
| `0x020C7814` | remapped entry to launch scene | `0x11`, `0x10`, `0x6e` |
| `0x020C785C` | remapped entry to instruction-gate bit | 0, 1, 4 |

The menu has other mode-dependent arrays; only this normal Training branch is
claimed. No repeated exercise descriptor structure or launch-function-pointer
array was established. Resource loaders do use indirect callbacks; those are
not evidence of an exercise registry.

`0x0204D790` has two range-checked code-branch tables for old cleanup and new
initialization (`0..0x8c`), at `0x0204D7B0` and `0x0204E35C`. The frame update
has another at `0x0204FC84`. These are ARM branch instructions selected by
`ADDLS PC,PC,index,LSL #2`, **not arrays of C function pointers**.

| Scene | Cleanup case | Init case | Update case | Relevant direct calls |
| --- | --- | --- | --- | --- |
| 3, `0x41` | `0x0204DA14` | `0x0204E5B4` | `0x0204FEC8` | common UI allocation; `0x020610B4`, `0x0205CDBC` |
| `0x43` | `0x0204DF48` | `0x0204EE18` | `0x02050088` | shared countdown; no broader mapping attempted |
| `0x10`, `0x11` | `0x0204DB04` | `0x0204E670` | `0x0204FF18` | `0x02027A28`, `0x0202756C`; update `0x02026710` |
| `0x6e` | `0x0204DB34` | `0x0204E890` | `0x0204FF28` | `0x02085BA8`, `0x020857E0` |

Rules uses allocation size `0xea4`, with scene in object `+0xea0`; it loads the
selected launch scene at `0x0206444C` and calls `0x0205A150` for rules-specific
parameters. Object `0x020E9A00` is later freed/reused by exercise allocations:
same address does **not** imply same type or a universal exercise object.

## Dynamic evidence and calculation relationship

Normal raw taps: x20 `(166,75)`, x100 `(112,75)`, Reading `(60,75)`;
instruction More/Next `(240,152)`, Start `(117,96)`. Each comparison starts
from the identical menu checkpoint, not a previously selected exercise.

| Event | x20 | x100 | Reading |
| --- | --- | --- | --- |
| Gate call `020773A4 -> 0202C668` | R0=0, R1=0; cycle 1140473709, insn 206879681 | R0=0, R1=1; cycle 1140473753, insn 206879715 | R0=0, R1=4; cycle 1140473797, insn 206879749 |
| `02050264 -> 0204D790`, R0=`0x41` | seq 916, cycle 1160071600 | same | same |
| `0204E5D8 -> 020610B4`, R1=`0x41` | seq 1037, cycle 1160074113 | same | same |
| Rules `02064470 -> 0205A150` | R0=`0x11`, seq 1042 | R0=`0x10`, seq 1042 | R0=`0x6e`, seq 1042 |
| Start -> countdown `0x43` | seq 3394, cycle 1535412982 | seq 3395, same cycle | seq 3613, cycle 1760609895 |
| Countdown -> actual scene | `0x11`, seq 3751, cycle 1643474263 | `0x10`, seq 3752, same cycle | `0x6e`, seq 3970, cycle 1868670643 |
| Constructor | `0204E698 -> 02027A28`, seq 3770, cycle 1643476243, insn 271860566 | same call, seq 3771, cycle 1643476244, insn 271836091 | `0204E8C0 -> 02085BA8`, seq 3989, cycle 1868672626, insn 338671926 |

For both calculations, R0=`0x020E9A00`, R2=R3=0, stack extra argument=0;
R1 is 1 for x20, 0 for x100. The constructor stores R1 at object `+0`.
The same `0x0202756C` initializer loads `/data/Calculation/Calculation_ch.cmp`,
localized character assets and NCER/NANR/palette resources. In the bounded
setup routine beginning `0x020272FC`, instructions `0x0202736C..0x02027398`
select 20 when object mode is 1, otherwise 100 when the extra flag is zero;
there are other branches not generalized here. Live object `+0x3c` is exactly
20 versus 100. Thus **shared implementation with mode parameterization is
proven**, not just inferred from similar names. Final screens contain first
problems, with no handwriting input and no answers accepted.

Reading is genuinely distinct: allocation `0xbb8`; constructor R0=`0x020E9A00`,
R1=7, R2=1, R3=1, stack values 1 and 0. R1 is not asserted to be the exercise
identity; it comes from global `0x020DA3DC`. R2 comes from `0x020DA3D8`.
The constructor dynamically loads `/data/Text/msg_reading_%c.bmg`,
`/data/Text/text16.NFTR` and `/data/Text/r_syllables_us.dat` (normal font selected).
The alternate font reference `text20.NFTR` is static evidence only. Last
visible state is the first reading spread; **no page-turn, microphone, reading
answer or exercise completion input was supplied**. No text/signature/resource
decoding was attempted.

## Save observation and exception

Both calculation branches: zero logical write APIs, zero Flash commits,
unchanged H0 throughout selection, rules, countdown and initialization.
Reading selection through its initial font-choice instructions is also
save-free. Normal-font tap `(65,96)` at phase `07-normal-font` causes:

| Callsite / return | Target | Length | Source | System cycle |
| --- | --- | ---: | --- | ---: |
| `0x0202EAF0` / `0x0202EAF4` | `0x100` | 16 | `0x020E7100` | 1590887259 |
| `0x0202EB10` / `0x0202EB14` | `0x20100` | 16 | same | 1591740896 |

Both use API `0x0200DE78`. Accepted bytes: 32; changed bytes: four:
`0x105` and `0x20105`: 00 -> 01;
`0x10e` and `0x2010e`: 19 -> 18. Final isolated Reading Flash hash:
`85073d232c53ccfc19cc8f453dc3cd7900d9f1a10e4e2b211668aaf8effd83f1`.
The paired offsets differ by `0x20000`. Preference/settings classification is
supported by the exact font-choice transition and small mirrored payload;
no field names or checksum algorithm are claimed. No later launch write.

Independent old-byte replay exactly matches all captured live snapshots and
final ledgers. State import detaches ordinary battery write-through, so after
this write `live_matches_disk` is false and Flash dirty is 1; actual live Flash,
phase `after.sav` and savestate agree. No durable restart claim is made for
this incidental preference change. The original comparison save remains
unchanged, as do Task G/H captures. All three paused, identity-verified Task I
runner PIDs were stopped after capture. Do not repeat the font-choice action
when a strictly save-free comparison is required.

## Architecture assessment

**D: mixed**, high confidence for these three launch paths. Menu ordering,
launch scene and first-instruction bit are table-driven. Scene lifecycle and
per-frame dispatch are hardcoded branch/state machines, with direct
constructor/setup calls. The calculation family shares mode-controlled code;
Reading uses a separate object/resource path. A freely extensible exercise
registry, descriptor ABI and safe custom-scene exit contract are **not proven**.
Appending a table row alone would not establish initialization, cleanup,
rendering, result/save transport, availability or bounds checks for a new ID.

## Hookability: future candidates, not implementation

### 1. Scene lifecycle entry `0x0204D790` (preferred)

Intercept **before** old-scene cleanup, reached from `0x02050264`. Available:
CPU/mode, desired scene R0, old scene `0x020DA464`, chosen launch scene
`0x020DA3F0`, live profile/menu context and LR. Gate first proof narrowly to
ARM9 ARM, old=3, new=`0x41`, selected=`0x11`. This identifies a Calculations
x20 launch from Training, not unrelated dialogs using the same rules scene.
For a later exercise-specific boundary, old=`0x43`, new=`0x11` distinguishes
countdown completion. Common lifecycle point, not exclusive to Training.

Style: opt-in runner-side dispatch/instruction interception and scheduler-safe
pause/resume with a native presentation state. Advantage: pre-cleanup is a
clear reversible observation boundary and original rules/resources/input can
remain intact. Risks: continuation/BL return stack, ARM7 scheduling, stale
cached/link dispatch, reused heap objects, and confusing generic scene IDs
with exercise IDs. Returning by resuming the **original transition** appears
practical; replacing it and returning arbitrary result data is not proven.

### 2. Calculation constructor `0x02027A28`, callsite `0x0204E698`

Runs after countdown, for both x20/x100. R0 is newly allocated object,
R1 mode (1/0), remaining parameters and stack extra flag available; current
scene separates `0x11`/`0x10`. Style: exercise-family native wrapper/sidecar
around original constructor, followed by original setup. Good narrow family
boundary with proven mode relationship; not common to Reading. Risks: frame
update `0x02026710`, later teardown and game-owned rendering expect a fully
initialized `0xc34` object. Omitting initialization, replacing R0 with a host
pointer or fabricating completion is unsafe and not recommended.

### 3. Menu selection store `0x0207737C`

Publishes selected launch scene R6 to `0x020DA3F0`; R4 is menu object,
`+0x6c4` menu index, and table context is still live. Style: read-only
host instruction-site interception before handoff, retaining original state.
Advantage: closest to UI selection, before resources are torn down. Risks:
interior-instruction hooks, mode-specific remapping, first-use rule gating,
selection fade phases and potential repeat execution. Extending the numeric
tables is **not** a sufficient custom-exercise implementation.

### Actual framework constraints

The NDS runner's `runner/src/runtime_arm.cpp` dispatcher is authoritative,
not the shared standalone ARM runtime. `runtime_dispatch_impl` handles
cached/link resolution, mode alignment, slice yield, static guards, literal
transfers and Tier-3 fallbacks. Generated code also has direct/linked calls;
a wrapper around one exported `runtime_dispatch` function alone must not be
assumed to catch every intra-bank or interpreted instruction boundary.

Existing generated instruction/fast-yield machinery and Tier-3 retirement
paths expose runner-side observation points without editing generated C.
`g_runtime_break_pc` and debug `run_to_pc` exist, but terminal breakpoint and
instruction-bisector stops are **not proven safe reusable function hooks**;
mid-function call-return continuation must be validated. Task I observer is
Tier-3-only, and this task does not prove equivalent compiled-bank interception
or an existing public per-title hook registration API. Any future hook must
cover the chosen execution path explicitly and preserve normal behavior
when disabled. No hook, result replacement or custom exercise was implemented.

## Recommended Task J (proposal only)

Smallest useful proof: opt-in **pass-through launch rendezvous**, at
`0x0204D790`, conditioned old=3/new=`0x41`/selected=`0x11`.
From the same menu checkpoint, normal x20 selection pauses at that boundary,
shows a trivial ROM-free host/native panel, then dismissal resumes the exact
original transition. Use the game's normal Back action on the resulting
rules screen to return to Training; do not enter or complete an exercise.
First validate scheduler-safe continuation and original register/return-stack
preservation, initially on the already-understood forced-interpreter path.
Do not substitute a fake return or rely on a terminal breakpoint being resumable.

This tests menu-to-native handoff and safe return with no new exercise ID,
object ABI, save/result format, font preference, recognition replacement or
resource registry. It is smaller and safer than inventing a new guest scene.
It would **not** yet prove custom scoring, completion/save integration or
production static-bank hook coverage. Touch, Decuma, rendering, audio, RTC and
save transport remain original systems to reuse, not replacement targets.
Task J was not started.

## Reproduction, validation and local artifacts

ROM-free changes: this report; `tools/task_i/brainage_launch_trace.h`,
`restore_menu.py`, `install_diagnostics.py`, `analyze_dispatch.py`.
Ignored runtime edits: matching header plus include/pre-step call in
`local/ndsrecomp/runner/src/tier3.cpp`. Installer uses apply_patch, validates
the pinned HEAD and existing Task A/C anchors, and is idempotent.

```powershell
python tools/task_i/install_diagnostics.py --codex-executable <bundled-codex.exe>
$env:PATH="$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-a-runner --target nds_runner --parallel 2
python tools/task_i/restore_menu.py --source local/task-g/session-001/04-training-menu --out local/task-i/x20-001 --port 19855
python tools/task_g/capture.py --out local/task-i/x20-001 --label 00-menu --cycles 0 --savestate
python tools/task_g/capture.py --out local/task-i/x20-001 --label 01-select-x20 --tap 166 75 --cycles 150000000 --savestate
python tools/task_i/analyze_dispatch.py --rom "../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds" --root local/task-i --output local/task-i/dispatch-audit.json
```

New run/output names must not already exist. The restore helper requires the
verified source checkpoint and launches with the existing forced-Tier-3,
direct/FreeBIOS/generated-firmware, network-off configuration and A/C/I traces.
Ports 19855/19856/19857 were used. Each subsequent tap/action and settling
interval is retained in each phase's `summary.json`; none contains answer
strokes. No source checkpoint was rewritten. Build log: `local/task-i-build.log`.
Actual build: `build/task-a-runner/nds_runner.exe`.

Local-only evidence: `local/task-i/{x20-001,x100-001,reading-001}/`, including
`restore.json`, `selection-state.json`, calculation `initialized-state.json`,
`calls.jsonl`, `requests.jsonl`, `flash.jsonl`, phase snapshots/images/states;
derived audit: `local/task-i/dispatch-audit.json`. Raw data remains ignored and
is not staged. Script syntax checks, installer idempotence, independent Flash
replay, exact-ROM table decoding and all three bounded traces passed. No broad
framework tests or performance validation were run.

Normal sandbox command creation actually failed with
`helper_unknown_error: setup refresh had errors`. Supported per-operation
outside-sandbox requests worked through auto-review; no human approval prompts
were required and no approval infrastructure was modified. This environment
failure is recorded, not represented as an application/runtime failure.

Remaining limits: safe custom native control-flow return and static-bank hook
coverage require a future proof; no descriptor registry is established. Task H
picture-drawing/calendar issue remains untouched. No second exercise completed,
picture drawing, microphone input, ROM patch, save-semantic change, generated-C
manual edit, custom exercise implementation or Task J execution.
