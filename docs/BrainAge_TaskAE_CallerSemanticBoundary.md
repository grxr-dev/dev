# Task AE - original caller to the next phase-dispatch call

**FULL PASS.** Starting from the exact Task AD endpoint, one fresh real-SDL replay executed **nine original ARM instructions**, completing the short caller/return/phase-gate block. It halted at **02026B90 before BL 02026218 dispatch**. The new semantic routine, gameplay continuation and later state writes did not execute.

Authoritative prefix: Task AD `a8502da4a156cf4cee756ee85afc2e016533bab8`, branch `codex/brainage`. [Result JSON](BrainAge_TaskAE_Result.json). Evidence tier remains **forced Tier-3 original ARM interpreter**, exact 11 - 7 / recognized-4 context; no compiled parity claim.

## Read-only analysis and selected boundary

Before harness changes or extended execution, the SHA-1-verified selected ROM was independently decoded with Capstone. The Task AD hashed RAM/DTCM and full terminal CPU state supplied concrete stack return targets. Linear decoding stops at each return; bytes after 02025830 and 02026704 include literal-pool data and are not treated as fallthrough code. The phase-two alternatives were identified but not entered.

| PC / opcode | Decoded instruction | Actual next PC / effect |
|---|---|---|
| 02025830 / E8BD8010 | POP {r4,pc} | Return to 020266B8; SP adds 8 |
| 020266B8 / EA00000F | B 020266FC | Skips the alternative multi-slot loop |
| 020266FC / E3A00001 | MOV r0,#1 | Original publication function return value |
| 02026700 / E28DD008 | ADD sp,sp,#8 | Releases its local stack reservation |
| 02026704 / E8BD8070 | POP {r4,r5,r6,pc} | Return to 02026988; SP adds 16 |
| 02026988 / E1D801F0 | LDRSH r0,[r8,#10] | Reads phase=1 at 020E9A10 |
| 0202698C / E3500002 | CMP r0,#2 | NZCV becomes 1/0/0/0 |
| 02026990 / 1A00007D | BNE 02026B8C | Taken because phase is 1 |
| 02026B8C / E1A00008 | MOV r0,r8 | Supplies exercise pointer |
| **02026B90 / EBFFFDA0** | **BL 02026218** | **Observed but never dispatched** |

This is a semantic boundary rather than an arbitrary instruction count: the first new routine after the original correctness/publication returns dispatches on exercise phase. Its statically visible phase-one route includes a store at 0202624C to exercise +34 and a later call to 02025F78. Those effects were not safely bounded in AE, so the BL and entire callee remain forbidden. The upcoming +34 store writes DA; the current +34 is already DA, so no claim of a future value change is made.

Preflight froze all ten observations, opcodes, expected registers/flags and fixed reads before execution. The live allowlist accepts only the nine-instruction path and rejects the terminal call at every index. The hook runs before bank handoff/count/fetch/Interpreter::step and preserves unwind at the stop. No original instruction or state was synthesized; generated ROM-derived C was untouched.

## Register and stack audit

The first 47 observations exactly match Task AD, including every PC/opcode/register/flag/instruction ordinal. Immediate slice-before main RAM and DTCM are byte-identical to AD's stop.

First POP reads 027E3B14=1 into r4 and 027E3B18=020266B8 into PC. These match the original consumer's PUSH captured in the retained prefix. Second POP reads 027E3B24=3 into r4, 027E3B28=0 into r5, 027E3B2C=72 into r6 and 027E3B30=02026988 into PC. All stack words were independently read from AD's hashed DTCM, validated live, and confirmed by the resulting registers. No stack word was modified.

SP path: **027E3B14 -> 027E3B1C -> 027E3B24 -> 027E3B34**. Net changes are r4 **1 -> 3**, r5 **020E9A00 -> 0**, SP **027E3B14 -> 027E3B34**, PC **02025830 -> 02026B90**. r0 transiently becomes 1 and is restored to 020E9A00 before the stop. r6 remains 72. All other registers, including LR=0, are unchanged. CMP changes N/Z/C/V from **0/1/1/0 to 1/0/0/0**; no mode/Thumb/interrupt-mask change occurs. The full per-instruction register/flag trace is in JSON.

At the unexecuted call, r0=020E9A00, r1=1, r2=4, r3=0, SP=027E3B34, LR=0. Only r0's exercise-pointer role is established; residual r1-r3 are not assigned invented ABI meanings. If the BL is later authorized, it would set LR=02026B94 and PC=02026218.

## State, save and timing

Immediate new main RAM diff: **0 bytes across all 4 MiB**. Immediate new DTCM diff: **0 bytes across all 16 KiB**. There are no memory-write instructions in the new slice; its only reads are bounded DTCM stack words and the phase halfword in main RAM. No guest MMIO/Flash/save operation or unbounded call is executed.

Delay +20, result flag +504, correct count +44 and phase +10 all remain **1 -> 1**. Score/progression/history/result-completion state has no new RAM/DTCM mutation; guest video, scene and touch remain unchanged. The prior FF->04 input staging, two acceptance stores, and 13 PUSH-related DTCM byte changes remain exclusively prefix effects. Native touch/presentation owners and private recognizer were already cleaned up. No gameplay resume or full answer completion is claimed.

Main RAM before/after SHA-256 `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9`; DTCM before/after `e2ab6955f9cfa7e43239c75a004e386609c55a282d291c6a286ea97954e062ff`.

Save remains byte-identical, SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; logical requests **0**, Flash commits **0**, changed bytes **0**, dirty=false. Original source checkpoint/save are unchanged.

ARM9 ordinals **281097880 -> 281097889** prove exactly nine new dispatches; cycles **3416875394 -> 3416875425** (+31). ARM7 ordinal stays **96026779**, while its scheduler cycles advance **1708437638 -> 1708437703** (+65). Unlike the shorter AD stop, this slice crosses normal scheduler accounting. Existing scheduler.cpp run_slice has a guest-HALT path that advances cycles without retiring instructions. The observed time change is reported; no counters were restored. The exact ARM9 path and exhaustive memory/video/save comparisons exclude an additional guest instruction or state mutation in the audited domains. This is not a claim that all scheduler/device internal bookkeeping stayed frozen.

## Checks and reproduction

Focused AE/AD guards, opcode negative cases, terminal/callee rejection, ordinal/path/predicate checks, unchanged publication policy and production-source checks pass. A fresh disabled control performs no recognition/publication/correctness or SDL input and has zero RAM/save changes. The enabled and disabled processes exit 0 without forced cleanup. Offline analysis validates the exact AD prefix, all newly executed instructions/states, stack reads, complete memory diffs and save/source identities. Build passed with existing historical Task S warnings only.

Only tools/task_ae and this ROM-free report/result are changed. Prior Brain Age and Inbox artifacts remain unchanged. Raw ROM/disassembly, RAM, save/checkpoint, screenshots and runner remain local/ignored. Runner SHA-256 `b80e50dea69df69420d10a96d944a7108d900c9e56ce099fb96e707611fe18f7`.

Audit retained evidence before rebuilding changes the runner hash:

```powershell
python tools/task_ae/preflight.py
python tools/task_ae/check.py
python tools/task_ae/analyze.py --out local/task-ae/session-001 --disabled local/task-ae/disabled-001 --export docs/BrainAge_TaskAE_Result.json
```

For a separately authorized fresh disposable reproduction:

```powershell
python tools/task_ae/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ae/build.ps1
python tools/task_ae/check.py
python tools/task_ae/run.py --out local/task-ae/disabled-FRESH --disabled --port 19941
python tools/task_ae/run.py --out local/task-ae/session-FRESH --port 19942
python tools/task_ae/analyze.py --out local/task-ae/session-FRESH --disabled local/task-ae/disabled-FRESH --export docs/BrainAge_TaskAE_Result.json
```

Uses existing selected ROM/BIOS/runner arguments, immutable Task G checkpoint, frozen Task Y SDL input, retained AD images and installed Capstone/toolchain. No second ROM workflow.

Recommended AF boundary: first analyze and bound the phase-one callee at **02026218**, starting with the unexecuted BL at **02026B90**, with the +34 store and later 02025F78 call explicitly identified. **Task AF has not started.**
