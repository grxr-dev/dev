# Task AB ? one decoded instruction beyond Task AA

**FULL PASS.** One fresh real-SDL causal replay reached the exact Task AA pre-state. After independent decode and live validation, original ARM instruction **0202573C / 05801504** executed once. The process halted with successor PC **02025740**, before dispatch of that instruction. The answer was not completed and gameplay was not resumed.

Predecessor: Task AA `6fad6ffde7b71e16fb3e1592287eccc24e9114fc`; branch `codex/brainage`. Exact ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. [Machine-readable result](BrainAge_TaskAB_Result.json).

## Instruction identification before execution

`preflight.py` read the SHA-1-verified selected ROM and independently decoded the instruction with Capstone. Its bytes agree with the retained local Task Z disassembly and Task AA's recorded opcode/pre-state. No generated ROM-derived C was edited.

- Opcode: **05801504**; decoded **STREQ r1,[r0,#0x504]**.
- Condition: EQ, with live Z=1; NZCV=0/1/1/0.
- ARM single-data-transfer encoding: immediate positive pre-indexed **word store**, no writeback, no PC destination.
- Base r0=`020E9A00`, source r1=1, immediate offset `504` (1284 decimal).
- Effective address: **020E9F04**, inside the audited exercise/main RAM; four-byte value is initially 0.
- Direct field: exercise **+504**, the established result flag.
- Normal successor: **02025740**; its independently checked opcode is `028DD004` (`ADDEQ sp,sp,#4`). This successor is forbidden.

These facts were frozen locally before the enabled run. Immediately before dispatch, the hook checked the actual opcode's addressing bits, registers, condition, target bounds/value and successor identity again, then logged `instruction_identified` and captured full RAM, DTCM, Flash and CPU pre-state. Any contradiction would halt before execution.

## Exact bounded extension

The unchanged frozen input digest is `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`. The two strokes contain the same 5+3 points: `(190,110),(156,91),(121,65),(121,98),(121,130)` then `(173,114),(132,114),(75,114)`. All ten events used `SDL_PushEvent -> normal mapping -> nds_set_touch -> native owner`. Candidates remained 2 then 4, with zero custom guest touch deliveries. Recognition was torn down before original publication/correctness.

The first **44 pre-dispatch observations** exactly match Task AA, including every register, flag, opcode, PC and instruction ordinal. The immediate pre-instruction 4 MiB RAM snapshot is byte-identical to Task AA's terminal snapshot.

| PC | Action |
|---|---|
| `02025734` | Prior AA MOVEQ sets r1=1 |
| `02025738` | Prior AA store sets delay +20=1 |
| **`0202573C`** | **AB permits the decoded result-flag store exactly once** |
| **`02025740`** | **Terminal observation only; never dispatched** |

The fixed allowlist has 45 observations and 44 dispatches. `dispatches()` rejects the successor at every index. The hook runs before interpreter count/fetch/step, validates post-state, calls terminal halt, returns 2 and preserves unwind. SDL terminal handling closes the disposable process. No guest synthetic return or counter restoration occurs.

The new interval advances ARM9 ordinal **281097877 -> 281097878** and cycles **3416875383 -> 3416875386**: one instruction, three cycles. r0..r14 and all flags remain identical. PC alone advances 0202573C -> 02025740. SP remains **027E3B04**, proving the successor stack adjustment did not occur. Both enabled and disabled processes exited 0 without forced cleanup.

## Immediate mutation audit

| State | Immediately before -> after AB instruction |
|---|---|
| Result flag +504 / 020E9F04 | **0 -> 1** |
| Result delay +20 | **1 -> 1** |
| Correct count +44 | **1 -> 1** |
| Phase +10 | **1 -> 1** |
| All 4 MiB main RAM | Exactly one changed byte: 020E9F04, 00 -> 01 |
| Full 16 KiB DTCM / stack | Byte-identical |
| Registers except PC / flags | Identical |
| Manager / slot / guest video / scene / touch | Unchanged |
| Downstream routine entries | **0** |

The instruction writes four bytes `00 00 00 00 -> 01 00 00 00`; only its low byte changes. The whole decision interval additionally retains AA's earlier delay byte and Z's submitted-units byte plus the same 13 changed PUSH bytes in DTCM. These are explicitly separated from the new AB mutation, and the PUSH writes reconstruct the full DTCM after image exactly.

Score, progression and history remain bounded by exhaustive RAM/DTCM comparisons and the fixed original entry path: no additional bytes change, and no downstream acceptance/progression/history/save routine executes. Undocumented field offsets are not invented. ARM7 counters remain fixed across the extension; no scheduler/device execution occurs between the isolated decision observations.

All source/live/disposable Flash snapshots remain byte-identical, SHA-256 **a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb**. Logical requests **0**, Flash commits **0**, changed bytes **0**, dirty=false. Source checkpoint remains immutable.

## Checks, artifacts and limits

Focused checks pass: fixed-decode/operand negative cases; AA-prefix parity; ordinal/repeated-entry/wrong-predicate/downstream rejection; successor rejection at every index; original AA guard; existing publication policy; unchanged production host/service sources; pre-dispatch hook ordering. The disabled read-only control has no input, recognition, publication, correctness, RAM change or save activity. Offline analysis validates the entire causal trace, immediate diff, prefix and save equality.

Only ROM-free `tools/task_ab/` and derived report/JSON are committed. Raw ROM/disassembly, checkpoints, RAM/save snapshots, window captures and generated runner remain local/ignored. Task AA source/evidence and production host/service were unchanged. Runner SHA-256: `e2d020934005cff518d0253faf0bc39e48b1b6fa4c555206f7e2df6af6c3bc74`.

Evidence tier is **forced Tier-3 original ARM interpreter**, for this one exact 11 - 7 / recognized-4 context. There is no compiled acceptance parity, general answer completion or later progression claim. Apart from the one new instruction and its direct flag byte, the causal guest state matches AA; host hold presentation counts may vary by timing (this run also recorded 159).

Offline reproduction of this completed evidence:

```powershell
python tools/task_ab/preflight.py
python tools/task_ab/check.py
python tools/task_ab/analyze.py --out local/task-ab/session-001 --disabled local/task-ab/disabled-001 --export docs/BrainAge_TaskAB_Result.json
```

For a separately authorized fresh disposable run, use new directories:

```powershell
python tools/task_ab/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ab/build.ps1
python tools/task_ab/check.py
python tools/task_ab/run.py --out local/task-ab/disabled-FRESH --disabled --port 19911
python tools/task_ab/run.py --out local/task-ab/session-FRESH --port 19912
python tools/task_ab/analyze.py --out local/task-ab/session-FRESH --disabled local/task-ab/disabled-FRESH --export docs/BrainAge_TaskAB_Result.json
```

The selected ROM/BIOS/runner arguments and immutable checkpoint are reused from existing local project manifests; Capstone and the existing local toolchain are required. Audit retained evidence before a later rebuild changes the executable hash. The completed enabled invocation is not repeated automatically.

**Stopped after Task AB. No successor instruction, answer completion, count/phase progression, score/history/save/menu integration, optimization or Task AC.**
