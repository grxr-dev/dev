# Task AK ? dynamic inner-helper boundary

**FULL PASS.** The independently reconstructed AI endpoint followed AJ's exact **25-instruction** path. Halted at **0x02067BDC before dispatch** of `E5842254 / STR r2,[r4,#0x254]`. Its effective target `0x020EA1C4` (exercise+0x7C4) remains **1**. No later instruction, full helper return or gameplay continuation ran. Task AL was not started.

[Machine-readable evidence](BrainAge_TaskAK_Result.json) records all 26 observations (25 dispatches plus terminal), every architectural read/write, all CPU deltas and all 28 changed DTCM bytes. Raw images/logs/window captures remain ignored under `local/task-ak/`.

## Provenance and exact start

AJ `a1d2c76baedc0ae841086eeccaf9aa5daebe8d16`, AI `5e086cb667a87d41eda1aec016e6418a57f64356`, AH `2b846d5ddeb751c59f02caa1aacd227d016a9b24`; branch `codex/brainage`. Initial repository HEAD was AJ. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. AJ's read-only certificate revalidated the exact ROM and retained AI RAM/DTCM/save/checkpoint, decoded words, CPU and predecessor artifacts against their authoritative commits. AJ sources/reports also match their commit. No generated ROM-derived C was edited.

The original Task G checkpoint SHA-256 `3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f` was restored by the existing deterministic machinery; no CPU/object state was fabricated. The frozen Task Y input digest `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32` remains unchanged: first stroke `(190,110),(156,91),(121,65),(121,98),(121,130)`; second `(173,114),(132,114),(75,114)`, each with release. Ten ordinary SDL queue events passed through frontend mapping and the native touch owner; recognizer candidates remained 2 then 4, with zero custom guest touch deliveries. Private service teardown preceded the original publication prefix. All held CPU/RAM/counters/video/save invariants passed.

All **66 AI observations** match the retained AI audit exactly, including registers, flags, opcodes, PCs and instruction ordinals. The entire earlier prefix is therefore reproduced. At arming: r0-r12=`020E9A00,1,4,0,020E9A00,0,72,0,020E9A00,0,0,0,0`; SP=`027E3B2C`, LR=`02026B94`, PC=`02026254`; NZCV=`1/0/0/0`, T=0, System mode=31, I=F=0. ARM9 ordinal=`281097899`, cycles=`3416875451`; ARM7 ordinal=`96026779`, cycles=`1708437703`.

Runtime gates verify all 16 registers, complete flags/mode/interrupt masks, main-RAM/DTCM/save hashes and accounting before arming, plus all 26 fixed instruction words including the forbidden terminal instruction. Mapped field values are implied by the full-image identity and independently decoded by the audit.

## Actual original path

| Index | PC | Opcode | Independently decoded original instruction | Dispatch |
|---|---|---|---|---|
| 0 | 0x02026254 | EBFFFF47 | bl #0x2025f78 | yes |
| 1 | 0x02025F78 | E92D41F0 | push {r4, r5, r6, r7, r8, lr} | yes |
| 2 | 0x02025F7C | E24DD008 | sub sp, sp, #8 | yes |
| 3 | 0x02025F80 | E1A07000 | mov r7, r0 | yes |
| 4 | 0x02025F84 | E5971040 | ldr r1, [r7, #0x40] | yes |
| 5 | 0x02025F88 | E597001C | ldr r0, [r7, #0x1c] | yes |
| 6 | 0x02025F8C | E2415001 | sub r5, r1, #1 | yes |
| 7 | 0x02025F90 | E3500000 | cmp r0, #0 | yes |
| 8 | 0x02025F94 | E5976034 | ldr r6, [r7, #0x34] | yes |
| 9 | 0x02025F98 | 0A00000C | beq #0x2025fd0 | yes |
| 10 | 0x02025FD0 | E5971040 | ldr r1, [r7, #0x40] | yes |
| 11 | 0x02025FD4 | E597003C | ldr r0, [r7, #0x3c] | yes |
| 12 | 0x02025FD8 | E1510000 | cmp r1, r0 | yes |
| 13 | 0x02025FDC | AA000019 | bge #0x2026048 | yes |
| 14 | 0x02025FE0 | E0871101 | add r1, r7, r1, lsl #2 | yes |
| 15 | 0x02025FE4 | E5910054 | ldr r0, [r1, #0x54] | yes |
| 16 | 0x02025FE8 | E3500009 | cmp r0, #9 | yes |
| 17 | 0x02025FEC | CA000002 | bgt #0x2025ffc | yes |
| 18 | 0x02025FFC | E3A01000 | mov r1, #0 | yes |
| 19 | 0x02026000 | E1A02001 | mov r2, r1 | yes |
| 20 | 0x02026004 | E2870E57 | add r0, r7, #0x570 | yes |
| 21 | 0x02026008 | E3A0301F | mov r3, #0x1f | yes |
| 22 | 0x0202600C | EB0106F0 | bl #0x2067bd4 | yes |
| 23 | 0x02067BD4 | E92D4010 | push {r4, lr} | yes |
| 24 | 0x02067BD8 | E1A04000 | mov r4, r0 | yes |
| 25 | 0x02067BDC | E5842254 | str r2, [r4, #0x254] | **NO ? terminal** |

The outer BL landed at 02025F78 with LR=02026258. BEQ was taken to 02025FD0 after CMP 0,0; BGE was dispatched but its GE condition failed after CMP 1,20, so it fell through to 02025FE0; BGT was taken to 02025FFC after CMP 11,9. The nested BL landed at 02067BD4 with LR=02026010. Each actual successor and its complete CPU state matched the predeclared AJ-derived model before the next instruction could dispatch.

## CPU delta

| Register | AI start | AK stop |
|---|---|---|
| r0 | 0x020E9A00 | 0x020E9F70 |
| r1 | 0x00000001 | 0x00000000 |
| r2 | 0x00000004 | 0x00000000 |
| r3 | 0x00000000 | 0x0000001F |
| r4 | 0x020E9A00 | 0x020E9F70 |
| r6 | 0x00000072 | 0x000000DA |
| r7 | 0x00000000 | 0x020E9A00 |
| SP | 0x027E3B2C | 0x027E3B04 |
| LR | 0x02026B94 | 0x02026010 |
| PC | 0x02026254 | 0x02067BDC |

Final r0-r12=`020E9F70,0,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B04`, LR=`02026010`, PC=`02067BDC`. r5, r8-r12 remain unchanged. NZCV changed `1/0/0/0 -> 0/0/1/0`; intermediate comparison flags were also checked. T=0, mode=31, I=F=0 throughout. No unexplained register/flag change.

## Memory and architectural events

The actual interpreter bus reported **eight ordered 32-bit writes**, all from the two original PUSH instructions. The before-bus firewall requires exact PC, event order, address, width, source value, existing word, source register and instruction ordinal. The after-bus hook checks readback and records each event; it updates only the host-side expected DTCM projection. It never writes a projected value to guest memory.

| Write PC | Address | Source | Before word | After word | Changed bytes |
|---|---|---|---|---|---|
| 0x02025F78 | 0x027E3B14 | r4 | 0x00000001 | 0x020E9A00 | 4 |
| 0x02025F78 | 0x027E3B18 | r5 | 0x020266B8 | 0x00000000 | 4 |
| 0x02025F78 | 0x027E3B1C | r6 | 0x00000000 | 0x00000072 | 1 |
| 0x02025F78 | 0x027E3B20 | r7 | 0x02067524 | 0x00000000 | 4 |
| 0x02025F78 | 0x027E3B24 | r8 | 0x00000003 | 0x020E9A00 | 4 |
| 0x02025F78 | 0x027E3B28 | lr | 0x00000000 | 0x02026258 | 4 |
| 0x02067BD4 | 0x027E3B04 | r4 | 0x00000000 | 0x020E9A00 | 3 |
| 0x02067BD4 | 0x027E3B08 | lr | 0x00000001 | 0x02026010 | 4 |

**32 written bytes; 28 changed bytes.** Complete 16 KiB DTCM comparison allows exactly these resulting changes and nothing else. The SUB reserves 027E3B0C..027E3B13 without writing it; that range remains unchanged. DTCM SHA-256 before `ffebd1000bf8222fd3b1224bfed4f6596f4288e38b82d6c22b1aa6c14bc37547`, after `1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716` matches AJ's prediction.

Complete 4 MiB main RAM is **byte-identical**: SHA-256 `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9` before and after. Exercise, manager and slot snapshots are unchanged. There were zero object/global writes, including idempotent writes, during AK. AH's earlier +34 store belongs to the reconstructed prefix, not AK.

The read firewall permits only the current fixed 32-bit instruction fetch or the six exact predeclared object loads. Observed events were **25 fetches + 6 object reads**; no unknown read class, DTCM data read or MMIO. The forbidden terminal instruction was not fetched through the interpreter bus. Debug peeks used to validate words/snapshots are read-only diagnostic observations, not guest instruction dispatches.

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
| 0x7c4 | 1 | 1 |

Delay/flag/count/phase remain **1/1/1/1**. +7C4 remains **1** despite the pending store's source being zero. Score, progression, history, result-completion and gameplay-resume state did not change in this stack-only slice. Unknown fields retain offset-based descriptions; no semantic naming is inferred beyond prior evidence.

## Persistence, accounting and stop guarantee

Save before/after SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; changed bytes **0**, logical save requests **0**, Flash commits **0**, dirty=false. Source checkpoint/save remain unchanged. Guest video, touch delivery, ownership and scene identity remain unchanged across AK. No peripheral effect attributable to AK or broad gameplay continuation.

ARM9 ordinal **281097899 -> 281097924 (+25)**; cycles **3416875451 -> 3416875512 (+61)**. ARM7 ordinal **96026779 -> 96026779 (+0)**; cycles **1708437703 -> 1708437703 (+0)**. Counters were never restored or synthesized. Private recognizer instruction counts are separate from these runtime counts.

The opt-in hook is before bank handoff, instruction accounting, decoder fetch and Interpreter::step. Ordered PC/opcode/CPU/instruction-count guards reject divergent paths before dispatch; read/write guards reject accesses before the underlying bus operation. At terminal observation 90 (AK index25), the hook checks final operands, eight completed writes and complete images, proves dispatch permission false, saves evidence, halts and unwinds. Final ARM9 ordinal is exactly the predicted +25. No successor or forbidden STR was executed.

The disabled control restores the same source checkpoint, exits before publication/input, and proves zero staged stores or decision dispatches, unchanged RAM/save, no SDL input, clean exit. This is an equivalent negative control against a harness-produced downstream mutation.

## Focused validation and reproduction

Nine focused check groups pass: compiled AK guard negatives; predecessor AI guard; existing publication policy; unchanged production host/service/exercise/policy; pre-dispatch hook; one underlying bus call per access; hook ordering; AK bus firewall; all 26 compiled CPU/opcode states matching the frozen model. The runner build passes; only pre-existing historical Task S indentation warnings appeared. Disabled and enabled real-SDL runs pass, followed by complete evidence audit. No unrelated regression matrix was run.

Use fresh local output directories (existing session evidence is never overwritten):

```powershell
python tools/task_ak/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ak/build.ps1
python tools/task_ak/check.py
python tools/task_ak/run.py --out local/task-ak/disabled-repro --disabled --port 20001
python tools/task_ak/run.py --out local/task-ak/session-repro --port 20002
python tools/task_ak/analyze.py --out local/task-ak/session-repro --disabled local/task-ak/disabled-repro --export local/task-ak/repro-result.json
```

Existing ignored source checkpoint, selected exact ROM, prior retained evidence, pinned framework, compiler, SDL runner build tree and window helper are required, as in AI. No user-supplied guest PC/register/call interface is introduced.

## Artifacts, scope and limits

Only `docs/BrainAge_TaskAK_DynamicInnerHelperBoundary.md`, `docs/BrainAge_TaskAK_Result.json` and `tools/task_ak/` are repository changes. Helpers comprise `expected.json`, `guard.h`, `guard_test.cpp`, `diagnostic.h`, `task_ak_decision.inc`, `install.py`, `build.ps1`, `preflight.py`, `run.py`, `check.py` and `analyze.py`. Installed runner hook/header changes are opt-in ignored local diagnostic infrastructure; generated ROM-derived C remains untouched. ROM/data/save/checkpoint/dumps/screenshots/binaries are not committed. Unrelated `jarvis-inbox-v1.zip` is preserved.

Evidence tier is **forced Tier-3 exact-context original ARM interpreter**, not compiled parity. This establishes only the frozen AI context and bounded prefix; no whole-routine return, general gameplay acceptance, scoring, progression/history/save behavior or semantic meaning of +7C4 is claimed.

Next smallest task, only if separately authorized: audit and execute just the first value-changing store at **02067BDC**, exercise+7C4 **1 -> 0**, with a pre-dispatch stop at its successor. **Stopped after AK; Task AL not started.**
