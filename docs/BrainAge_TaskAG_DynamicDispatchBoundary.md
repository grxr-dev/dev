# Task AG - dynamic validation of AF outer dispatch prefix

**FULL PASS.** One fresh frozen real-SDL replay reconstructed the complete authoritative AE state. Exactly **eight original ARM instructions** then matched AF's prediction. Execution halted at **0202624C before the STR dispatched**. Only the two predicted stack words changed; no main-RAM/object, mapped gameplay field or save change occurred.

AF: `63ff0c59f995fe9e2df57248ef261d1f4c8c6819`; AE: `6a43d5bfa4c85773b0f986b9d73944ab5e01700e`; AD: `a8502da4a156cf4cee756ee85afc2e016533bab8`. Branch `codex/brainage`. [Result JSON](BrainAge_TaskAG_Result.json).

## Identity and fail-closed start gate

Exact selected ROM SHA-1: `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. AF's read-only verifier passed without guest execution. AG preflight verifies committed AF/AE reports, all retained AF input hashes, ROM words against AE RAM, full AE CPU state, fields, save/checkpoint hashes and independently decoded instructions. The expected states and PUSH footprint were frozen before the dynamic run.

The driver reuses the existing immutable Task G checkpoint and Task Y frozen input (`88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`), through ten real SDL events and the native touch owner. Recognition remains 2 -> 4, with zero custom guest touch deliveries. Private recognizer cleanup precedes original publication/correctness. No direct guest state fabrication or diagnostic candidate injection is used.

All **56 AE pre-dispatch observations** match the authoritative AE trace exactly: PCs, instruction words, registers, flags and ARM9 ordinals. At the first AG instruction, the live gate checks every register, NZCV/T/mode/I/F, complete 4 MiB RAM and 16 KiB DTCM hashes, mapped fields and every expected instruction word before permitting the BL. Fresh live RAM/DTCM equal the preserved AE terminal images byte for byte. Source checkpoint SHA-256 remains `3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f`.

## Exact dynamically executed path

| PC / opcode | Original instruction | Observed control-flow result |
|---|---|---|
| 02026B90 / EBFFFDA0 | BL 02026218 | PC=02026218; LR=02026B94 |
| 02026218 / E92D4010 | PUSH {r4,lr} | SP=027E3B2C; two stack words written |
| 0202621C / E1A04000 | MOV r4,r0 | r4=020E9A00 |
| 02026220 / E1D401F0 | LDRSH r0,[r4,#10] | r0=phase halfword 1 |
| 02026224 / E3500005 | CMP r0,#5 | NZCV=1/0/0/0 |
| 02026228 / 908FF100 | ADDLS pc,pc,r0,LSL #2 | LS true; 02026230 + 4 = 02026234 |
| 02026234 / EA000003 | B 02026248 | Exact phase-one table-slot branch |
| 02026248 / E3A000DA | MOV r0,#DA | r0=000000DA; flags preserved |
| **0202624C / E5840034** | **STR r0,[r4,#34]** | **Terminal observation only; never dispatched** |

The fixed decision path has 64 observations and 63 dispatches, of which exactly eight are new beyond AE. The terminal STR is rejected by dispatches() at every index. Unexpected PCs, opcode/register changes, repeated entries, ordinals, alternate table slots, later instructions and inner calls fail before dispatch. The terminal hook precedes bank handoff/count/fetch/Interpreter::step, halts and preserves unwind. Both enabled and disabled processes exited 0 without forced cleanup. No instruction at 02026250 or inner BL 02026254 -> 02025F78 executed.

## CPU and memory effects

Final registers, all hexadecimal:

- r0-r3: **000000DA, 00000001, 00000004, 00000000**
- r4-r7: **020E9A00, 00000000, 00000072, 00000000**
- r8-r12: **020E9A00, 00000000, 00000000, 00000000, 00000000**
- SP / LR / PC: **027E3B2C / 02026B94 / 0202624C**
- NZCV **1/0/0/0**, T=0, System mode 31, I=F=0.

Deltas from AE: r0 **020E9A00 -> DA**, r4 **3 -> 020E9A00**, SP **027E3B34 -> 027E3B2C**, LR **0 -> 02026B94**, PC **02026B90 -> 0202624C**. All other registers and final flags are unchanged; every intermediate state matches AF. The CMP computes the predicted flags rather than preserving them by shortcut.

Main RAM: **0 changed bytes across all 4 MiB**, including code and all objects. DTCM: exactly the expected PUSH footprint **027E3B2C..027E3B33**, with **3 bytes differing across two written words**:

| Word address | Before -> after |
|---|---|
| 027E3B2C | 00000072 -> 00000003 |
| 027E3B30 | 02026988 -> 02026B94 |

Exact changed bytes: **027E3B2C: 72 -> 03**, **027E3B30: 88 -> 94**, **027E3B31: 69 -> 6B**. The remaining bytes, including all other stack storage, are unchanged. The live hook validates the exact expected bytes after PUSH at every subsequent instruction; it does not merely permit any write in a stack range.

Before/after mapped fields: phase +10 **1/1**, delay +20 **1/1**, result flag +504 **1/1**, correct count +44 **1/1**, unknown assigned word +34 **DA/DA**. The +34 store did **not** execute even though its source equals its current value. Other checks remain +1C=0, +3C=20 decimal, +40=1, +58=11 decimal, +4C=4, +51C=255 decimal, +38=0, +50C=255 decimal, +514=4 and +7C4=1. Unknown fields retain AF's mechanical labels; none is invented as score/history state.

No score/count/phase/progression/history/result-completion or gameplay-resume effect is observed: all main RAM and exercise/manager/slot images remain identical to AE. AG's only memory accesses are bounded DTCM PUSH writes and the exercise phase halfword read. Thus no AG instruction performs MMIO or Flash/peripheral access; video, touch and scene observations remain identical. This does not claim all normal scheduler internal bookkeeping is frozen.

Main RAM before/after SHA-256: `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9`. AE DTCM: `e2ab6955f9cfa7e43239c75a004e386609c55a282d291c6a286ea97954e062ff`; AG DTCM: `ffebd1000bf8222fd3b1224bfed4f6596f4288e38b82d6c22b1aa6c14bc37547`.

## Persistence, accounting and checks

Save byte-identical; before/after SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; changed bytes **0**, logical save requests **0**, Flash commits **0**, dirty=false. Original checkpoint/save remain unchanged. No historical state or half-accepted process is resumed after the stop.

- ARM9 ordinal **281097889 -> 281097897**: **+8 instructions**.
- ARM9 cycles **3416875425 -> 3416875447**: **+22**.
- ARM7 ordinal **96026779 -> 96026779**: **0 instructions**.
- ARM7 cycles **1708437703 -> 1708437703**: **0**.
- No counters restored; no unrelated scheduler investigation/refactor.

Focused tests passed: exact AE-prefix parity, opcode/every-register negative cases, exact ordinal/path budget, terminal STR/inner-call/alternate-path rejection at every index, PUSH byte validation, predecessor AE guard, unchanged publication policy and production sources, and pre-dispatch hook order. Fresh disabled control has zero input/publication/correctness and zero RAM/save changes. Offline analysis validates all input events, complete AE prefix, full AG trace, exact field/stack/RAM/save diffs and source identities. Build passed with only existing historical Task S warnings.

## Artifacts, limits and reproduction

Only tools/task_ag plus this report/result are added. Unrelated Inbox commits/files, AF/AE/AD source and evidence are preserved. ROM, database, RAM/save/checkpoint dumps, BIOS/firmware, screenshots, raw disassembly and generated C/binaries remain uncommitted. Runner SHA-256 `dc6e17ede51a9b07b7c3427a8810b21a513d43acb141cb52685c04e7312a2f22`.

Evidence tier: **forced Tier-3 exact-context original ARM interpreter**, one preserved 11 - 7 / recognized-4 input. No compiled parity or full routine/gameplay-completion claim. The first object store and all inner routines remain unexecuted.

Audit retained evidence before rebuilding changes the executable hash:

```powershell
python tools/task_ag/preflight.py
python tools/task_ag/check.py
python tools/task_ag/analyze.py --out local/task-ag/session-001 --disabled local/task-ag/disabled-001 --export docs/BrainAge_TaskAG_Result.json
```

For a separately authorized fresh bounded replay:

```powershell
python tools/task_ag/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ag/build.ps1
python tools/task_ag/check.py
python tools/task_ag/run.py --out local/task-ag/disabled-FRESH --disabled --port 19961
python tools/task_ag/run.py --out local/task-ag/session-FRESH --port 19962
python tools/task_ag/analyze.py --out local/task-ag/session-FRESH --disabled local/task-ag/disabled-FRESH --export docs/BrainAge_TaskAG_Result.json
```

Preflight requires retained AE/AF evidence and installed Capstone; driver/build reuse existing selected ROM/BIOS arguments and local toolchain. The completed enabled replay is not automatically repeated.

Next smallest task, only if separately authorized: audit the single idempotent STR at **0202624C** (+34, DA -> DA) and stop before **02026250**. Do not enter the inner BL. **Stopped after Task AG; Task AH not started.**
