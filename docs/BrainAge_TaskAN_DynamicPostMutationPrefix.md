# Task AN ? dynamic post-mutation prefix

**FULL PASS.** Reconstructed the complete AL prefix, independently revalidated its exact stop, dispatched exactly AM's **19 original ARM instructions**, then halted at **0x02067C44 before fetch/dispatch** of `E5840250 / STR r0,[r4,#0x250]`. No AN write occurred. Main RAM/DTCM/save remained byte-identical. **Task AO not started.**

[Machine-readable evidence](BrainAge_TaskAN_Result.json) contains all 20 AN CPU observations, exact original opcodes/decodes, every read event, all checked fields, hashes and accounting. Raw runtime evidence is ignored under `local/task-an/session-001` and `local/task-an/disabled-001`.

## Provenance and exact reconstruction

AM `cb2126cfa0c2e75714b993cdc0124c49c8e1b680`, AL `7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70`, AK `dd29b71e182611fb73016aa1a13367e70c9cd290`. Branch `codex/brainage`; initial HEAD included infrastructure-only commit `7612773249261ea45a023cf509b83fb583789dc1`, preserved. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; pinned framework `3a57236bb23d25dcb4caad7d58d733311062ff5e`.

Preflight runs AM's read-only certificate and checks committed AM/AL report/helper equality. The certificate revalidates authoritative predecessors, complete retained AL RAM/DTCM/save, CPU and ordinal, exact ROM words and immutable source checkpoint. The AN model takes its exact PCs/opcodes directly from committed AM, is frozen before the dynamic run, and has SHA-256 `378cc7e54a60e2cfd002dd2a5a09dd222582128743bee2ef8d145058f154de67`. Compiled guard constants are checked against that model.

Existing deterministic machinery restores Task G checkpoint SHA-256 `3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f` and the exact save, then replays the frozen Task Y SDL input digest `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`. It never fabricates guest registers or object fields. Ordinary SDL queue -> coordinate mapping -> native owner receives stroke0 `(190,110),(156,91),(121,65),(121,98),(121,130)`, release; stroke1 `(173,114),(132,114),(75,114)`, release. Ten SDL events yield original recognizer candidates2 then4 with zero custom guest touch deliveries. The private service is torn down before original publication. The existing private hold's CPU/RAM/counter/video/save isolation checks pass.

All **92 retained AL pre-dispatch observations** match exactly, including full registers/flags/opcodes/ordinals. The AL store at02067BDC is reconstructed as exactly one original architectural write, +7C4 1->0, and is outside AN. At AN arming, all16 registers, flags/mode/masks, complete RAM/DTCM/save hashes, ARM9/ARM7 ordinals/cycles and all20 instruction words (including forbidden terminal) match authoritative evidence.

AL start r0-r12 (hex): `020E9F70,0,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B04`, LR=`02026010`, PC=`02067BE0`; NZCV=`0/0/1/0`, T=0, System mode31, I=F=0. ARM9 ordinal281097925/cycles3416875515; ARM7 ordinal96026779/cycles1708437703.

## Exact executed control flow

| AN index | PC | Opcode | Original decode | Effect / condition |
|---|---|---|---|---|
| 0 | 0x02067BE0 | E3510000 | cmp r1, #0 | CMP 0,0 -> NZCV=0110 |
| 1 | 0x02067BE4 | E3A00000 | mov r0, #0 | r0=0; flags unchanged |
| 2 | 0x02067BE8 | 0A000004 | beq #0x2067c00 | EQ true Z=1 -> 02067C00; skips alternate r1 cases |
| 3 | 0x02067C00 | E3520000 | cmp r2, #0 | CMP 0,0 -> NZCV=0110 |
| 4 | 0x02067C04 | BA00000D | blt #0x2067c40 | LT false N=V=0; target 02067C40 not taken -> 02067C08 |
| 5 | 0x02067C08 | E3520008 | cmp r2, #8 | CMP 0,8 -> NZCV=1000 |
| 6 | 0x02067C0C | AA00000B | bge #0x2067c40 | GE false N=1 V=0; target 02067C40 not taken -> 02067C10 |
| 7 | 0x02067C10 | E3A00001 | mov r0, #1 | r0=1 |
| 8 | 0x02067C14 | E1A00210 | lsl r0, r0, r2 | r0=1 << r2(0) = 1; no flags |
| 9 | 0x02067C18 | E59410C0 | ldr r1, [r4, #0xc0] | object read [020EA030] (+630)=1 -> r1 |
| 10 | 0x02067C1C | E0110000 | ands r0, r1, r0 | r0=1 & 1=1; NZ=00; zero-shift carry preserved C=0, V=0 |
| 11 | 0x02067C20 | 0A000006 | beq #0x2067c40 | EQ false Z=0; target 02067C40 not taken -> 02067C24 |
| 12 | 0x02067C24 | E0841102 | add r1, r4, r2, lsl #2 | r1=020E9F70+(0 << 2)=020E9F70 |
| 13 | 0x02067C28 | E5910080 | ldr r0, [r1, #0x80] | object read [020E9FF0] (+5F0)=44 hex -> r0 |
| 14 | 0x02067C2C | E1530000 | cmp r3, r0 | CMP 1F,44 -> NZCV=1000; signed 31 < 68 |
| 15 | 0x02067C30 | B5911060 | ldrlt r1, [r1, #0x60] | LT true; object read [020E9FD0] (+5D0)=02131D24 -> r1 |
| 16 | 0x02067C34 | B3A00054 | movlt r0, #0x54 | LT true; r0=54 hex |
| 17 | 0x02067C38 | B0201093 | mlalt r0, r3, r0, r1 | LT true; r0=1F*54+02131D24=02132750; no flags |
| 18 | 0x02067C3C | BA000000 | blt #0x2067c44 | LT true N=1 V=0 -> 02067C44; skips MOV r0,0 |
| 19 | 0x02067C44 | E5840250 | str r0, [r4, #0x250] | **NOT DISPATCHED ? terminal** |

BEQ02067BE8 is taken to02067C00 (Z=1). BLT02067C04 and BGE02067C0C are condition-failed dispatched instructions, falling through. BEQ02067C20 fails (Z=0). Conditional LDRLT/MOVLT/MLALT execute with N=1,V=0; BLT02067C3C is taken to02067C44. Ordered full CPU/opcode checks at every observation prove these actual successors. No call, return, stack access or unbounded loop occurs in AN.

## CPU and read audit

| Register | AL before | AN after |
|---|---|---|
| r0 | 0x020E9F70 | 0x02132750 |
| r1 | 0x00000000 | 0x02131D24 |
| PC | 0x02067BE0 | 0x02067C44 |

Only r0,r1,PC change. Final r0-r12=`02132750,02131D24,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B04`, LR=`02026010`, PC=`02067C44`. NZCV changes `0/0/1/0 -> 1/0/0/0`; intermediate states0110,1000,0000,1000 are checked. T/mode/I/F and all other registers remain unchanged. No unexplained change.

Observed three data reads (all aligned32-bit ordinary main RAM):

| Read PC | Address | Width | Value |
|---|---|---|---|
| 0x02067C18 | 0x020EA030 | 4 | 0x00000001 |
| 0x02067C28 | 0x020E9FF0 | 4 | 0x00000044 |
| 0x02067C30 | 0x020E9FD0 | 4 | 0x02131D24 |

Together with19 instruction fetches, these are **22 exact ordered bus-read events**. PC/address/width/value/order/ordinal are checked before underlying access. Unknown, repeated, skipped or MMIO reads fail closed before any debug read of an unapproved address. No fetch at02067C44 occurred. The guard's word peeks and snapshots are read-only diagnostics, not guest dispatches.

## Memory, fields and persistence

**Zero architectural writes, zero main-RAM/object diff, zero DTCM diff.** Every observation compares all4MiB main RAM and all16KiB DTCM to the independently revalidated AL start. Before-bus hooks reject every write width before the underlying bus call. The report distinguishes no write events from no changed bytes; idempotent writes are also forbidden.

Main RAM SHA-256 before=after `9f31cfc87f6d2913f83bd98854c4837330dfdef539888c935f6b83aea0688dc9`. DTCM before=after `1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716`. Save before=after `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`. Source checkpoint/save are unchanged; final save was read from the disposable runner before exit, not synthesized by cleanup.

All requested fields and other AM-audited helper destinations remain unchanged:

| Exercise offset | Before | After |
|---|---|---|
| 0x10 | 1 | 1 |
| 0x20 | 1 | 1 |
| 0x34 | 0xDA | 0xDA |
| 0x44 | 1 | 1 |
| 0x1C | 0 | 0 |
| 0x3C | 20 | 20 |
| 0x40 | 1 | 1 |
| 0x58 | 11 | 11 |
| 0x4C | 4 | 4 |
| 0x504 | 1 | 1 |
| 0x51C | 255 | 255 |
| 0x38 | 0 | 0 |
| 0x50c | 255 | 255 |
| 0x514 | 4 | 4 |
| 0x7c4 | 0 | 0 |
| 0x630 | 1 | 1 |
| 0x5f0 | 68 | 68 |
| 0x5d0 | 0x2131D24 | 0x2131D24 |
| 0x7c0 | 0x2133A18 | 0x2133A18 |
| 0x7bc | 0x20EA034 | 0x20EA034 |
| 0x7e8 | 0 | 0 |
| 0x7c8 | 0x2D000 | 0x2D000 |
| 0x7cc | 0x60000 | 0x60000 |
| 0x7d0 | 0x1000 | 0x1000 |
| 0x7d4 | 0x1000 | 0x1000 |
| 0x7f8 | 0 | 0 |
| 0x7dc | 0 | 0 |
| 0x7e0 | 0 | 0 |
| 0x7fa | 0xFFFF | 0xFFFF |
| 0x7ec | 0 | 0 |
| 0x7f0 | 0xFFFFFFFF | 0xFFFFFFFF |
| 0x7d8 | 0 | 0 |
| 0x7e4 | 0 | 0 |
| 0x7f4 | 0 | 0 |

Delay/result flag/correct count/phase remain **1/1/1/1**. +7C4 remains0; +7C0 remains**02133A18**, despite pending source r0=02132750. Score/progression/history/result-completion/gameplay-resume state is unchanged in this read-only slice. Unknown fields retain offset-only semantics. No pointed-to data at02132750 is dereferenced.

Save changed bytes0; logical save requests0; Flash commits0; dirty=false. Actual AN bus MMIO accesses0; no peripheral effect attributable to the original AN instructions. Video/touch/scene/ownership observations remain unchanged. No gameplay resume, full helper return or later instruction was allowed.

## Accounting and stop proof

ARM9 ordinal: **281097925 -> 281097944**, delta **+19**.

ARM9 cycles: **3416875515 -> 3416875550**, delta **+35**.

ARM7 ordinal: **96026779 -> 96026779**, delta **+0**.

ARM7 cycles: **1708437703 -> 1708437767**, delta **+64**.


ARM7 executed zero instructions, but its cycle counter advanced64. This is reported as observed; no counters were restored, scheduler refactor performed or broader accounting investigation undertaken. Complete CPU/memory/read/save assertions show no state contradiction. An initial auditor incorrectly required zero ARM7 cycle delta; that unrequested condition was removed without changing runtime guards, frozen model or the authoritative run. No claim is made that all scheduler accounting is frozen.

The fixed opt-in control hook precedes bank handoff, instruction accounting, fetch and Interpreter::step. Exactly19 AN dispatches produce ordinal281097944. Terminal observation110 (AN index19) checks full CPU, all images, all22 reads and pending store operands, proves dispatch permission false, captures evidence, halts and unwinds. The forbidden STR and every later instruction remain unexecuted.

## Validation, reproduction and scope

Seven focused groups pass: AN positive/negative CPU/opcode/path/budget/read/write guards; predecessor AL guard; unchanged publication policy; hook order and single underlying bus call per width; compiled constants matching the frozen AM model; unchanged production host/service/exercise/policy; terminal-before-dispatch and write-before-bus firewall. Runner build passes with only pre-existing historical Task S indentation warnings.

Disabled control restores the same checkpoint, exits before publication/input, has no stage/decision dispatches, zero RAM/save changes and clean exit. Enabled replay and exhaustive prefix/CPU/bus/image/persistence audit pass. Both exit cleanly with no forced cleanup. No broad unrelated matrix was run.

Use fresh ignored output directories:

```powershell
python tools/task_an/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_an/build.ps1
python tools/task_an/check.py
python tools/task_an/run.py --out local/task-an/disabled-repro --disabled --port 20201
python tools/task_an/run.py --out local/task-an/session-repro --port 20202
python tools/task_an/analyze.py --out local/task-an/session-repro --disabled local/task-an/disabled-repro --export local/task-an/repro-result.json
```

Existing exact ROM, ignored Task G checkpoint and predecessor evidence, pinned framework, toolchain, build tree and process-window helper are required as in AL. Sources contain no arbitrary PC/register/call API. Generated ROM-derived C, ROM, checkpoints, RAM/save dumps, screenshots/assets and binaries are not committed.

Repository changes are only these two Task AN reports and `tools/task_an/`: expected.json, guard.h, guard_test.cpp, diagnostic.h, task_an_decision.inc, install.py, build.ps1, preflight.py, run.py, check.py and analyze.py. Installed opt-in runner instrumentation remains local/ignored. Unrelated infrastructure artifacts/commits and jarvis-inbox-v1.zip are preserved.

Evidence is **forced Tier-3 exact-context original ARM interpreter; no compiled parity**. It proves only this frozen recognized4 context and write-free slice, not whole-function/gameplay acceptance or unknown field semantics.

Next smallest task, only if separately authorized: audit/execute the pending **02067C44** word store at exercise+7C0, **02133A18 -> 02132750**, stopping before its successor. **Stopped after AN; Task AO not started.**
