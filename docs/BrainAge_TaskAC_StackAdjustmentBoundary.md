# Task AC - one stack-adjust instruction beyond Task AB

**FULL PASS.** One fresh frozen real-SDL replay reached the exact Task AB boundary. After independent decode and live validation, instruction **02025740 / 028DD004** executed once. The process halted at **02025744 before dispatch**. The successor POP did not execute; the answer was not completed and gameplay was not resumed.

Predecessor: Task AB `9b3396619e0b853ea8445929428beee6919aa15d`; branch `codex/brainage`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. [Machine-readable result](BrainAge_TaskAC_Result.json).

## Identification before execution

`preflight.py` independently decoded bytes from the SHA-1-verified selected ROM with Capstone and checked them against retained local Task Z disassembly and the committed Task AB pre-state. This is an instruction-level ROM/disassembly check; generated ROM-derived C was not edited.

- Exact opcode **028DD004**, decoded **ADDEQ sp,sp,#4**.
- Condition EQ; live Z=1, NZCV=0/1/1/0, ARM mode System (31), T=0.
- Source/destination register r13 (SP), initially **027E3B04**; immediate 4, rotation 0.
- Effect: **SP = 027E3B08**, adding four without an S-bit flag update.
- No memory address/write, branch, call or callee target. LR stays **0**.
- Normal successor PC **02025744**, independently checked opcode **08BD8030** (`POPEQ {r4,r5,pc}`). That successor remains forbidden.

The derived preflight was frozen before the enabled run. The live hook rechecked the actual ADD/immediate/Rn/Rd/S encoding, source SP, EQ predicate, LR and successor opcode before dispatch. It recorded `instruction_identified`, full registers/flags and immediate before RAM/DTCM/Flash images. A contradictory opcode/context would halt before execution.

## Causal replay and exact comparison

The frozen input SHA-256 remains `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`. The unchanged two strokes are `(190,110),(156,91),(121,65),(121,98),(121,130)` and `(173,114),(132,114),(75,114)`. All ten events used SDL_PushEvent -> normal frontend coordinate mapping -> nds_set_touch -> native owner -> isolated recognizer. Recognition remained 2 then 4, with no custom guest touch delivery. Private recognition was torn down before original publication/correctness.

The first **45 pre-dispatch observations** match Task AB exactly, including PCs, opcodes, every register, flags and ordinals. Immediate pre-AC main RAM and DTCM are byte-identical to Task AB's terminal images. Host hold presentation count was 160 here versus 159 in AB; this timing variation did not change guest causal state.

| Boundary | Observed action |
|---|---|
| 02025738 | Prior AA delay store |
| 0202573C | Prior AB flag store |
| **02025740** | **AC executes the validated ADD exactly once** |
| **02025744** | **Read-only stop observation; POP is never dispatched** |

The fixed path has 46 observations and exactly 45 dispatches. `dispatches()` rejects 02025744 at every index. The runtime hook precedes instruction counting/fetch/Interpreter::step. At the stop it validates state, calls terminal halt, returns 2, synchronizes CPU state and preserves unwind; SDL terminal handling closes the disposable process. No synthetic guest return, arbitrary guest-call API or counter restoration is used.

Immediate ARM9 ordinal **281097878 -> 281097879** and cycles **3416875386 -> 3416875387** advance by one instruction/one cycle. Pre/post PC is **02025740 -> 02025744**, SP **027E3B04 -> 027E3B08**, LR **0 -> 0**. All other registers and CPSR flags stay identical. Both the enabled run and disabled read-only control exited 0 without forced cleanup. No gameplay resume occurred.

## Immediate state audit

| State | Before -> after the AC instruction |
|---|---|
| Result delay +20 | **1 -> 1** |
| Result flag +504 | **1 -> 1** |
| Correct count +44 | **1 -> 1** |
| Phase +10 | **1 -> 1** |
| All 4 MiB main RAM | **Zero changed bytes** |
| Entire 16 KiB DTCM / stack memory | **Zero changed bytes** |
| Registers | Only SP and PC change |
| Flags / LR | Unchanged |
| Guest video / scene / touch / presentation | Unchanged across AC |
| Downstream routine entries/side effects | **0** |

Main RAM before/after SHA-256: `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9`. DTCM before/after: `e2ab6955f9cfa7e43239c75a004e386609c55a282d291c6a286ea97954e062ff`. The ADD adjusts a register; it does not erase or write the four bytes released from the stack frame.

Earlier Z/AA/AB effects remain separately explained: whole-decision RAM still has submitted-units FF -> 04, delay 0 -> 1 and result flag 0 -> 1, while DTCM retains the same 13 changed bytes reconstructed from the two original PUSH operations. None is a new AC mutation. Manager/slot and all remaining exercise bytes remain unchanged. Score/progression/history are excluded by the exhaustive immediate RAM/DTCM audit and exact instruction path; no speculative field offsets are assigned to them.

Save/source/live/disposable Flash remains byte-identical, SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`. Logical requests **0**, Flash commits **0**, changed bytes **0**, dirty=false. Source checkpoint stays immutable. ARM7 cycles/ordinal remain fixed across the decision and AC extension.

## Checks, limits and reproduction

Focused checks passed: fixed ADD/SP/condition and opcode negative cases; AB-prefix parity; repeated-entry/ordinal/wrong-path/downstream rejection; successor rejection at every index; predecessor AB guard; unchanged publication policy and production host/service source; pre-dispatch hook ordering. Offline analysis verifies every causal input, byte diff, register/flag delta, prefix, source and save. The disabled control has zero recognition/publication/correctness/input activity and zero RAM/save changes. Build succeeded with only existing historical Task S warnings.

Evidence tier is **forced Tier-3 original ARM interpreter**, limited to this exact 11 - 7 / recognized-4 context. No compiled acceptance parity, answer completion or later progression is claimed. Runner SHA-256: `e825395136476c1008f665ca7b9caa1131f0be38c4683ceb394a53205429ecfe`.

Only ROM-free tools/task_ac source/tests and derived report/JSON are committed. Raw ROM/disassembly, checkpoints, saves/RAM images, window captures and generated runner stay ignored under local/task-ac and build. Task AB source/evidence and production code are unchanged.

Offline reproduction of this completed evidence:

```powershell
python tools/task_ac/preflight.py
python tools/task_ac/check.py
python tools/task_ac/analyze.py --out local/task-ac/session-001 --disabled local/task-ac/disabled-001 --export docs/BrainAge_TaskAC_Result.json
```

For a separately authorized fresh disposable reproduction, use new output directories:

```powershell
python tools/task_ac/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ac/build.ps1
python tools/task_ac/check.py
python tools/task_ac/run.py --out local/task-ac/disabled-FRESH --disabled --port 19921
python tools/task_ac/run.py --out local/task-ac/session-FRESH --port 19922
python tools/task_ac/analyze.py --out local/task-ac/session-FRESH --disabled local/task-ac/disabled-FRESH --export docs/BrainAge_TaskAC_Result.json
```

The driver reuses the project's selected ROM/BIOS/runner arguments and immutable checkpoint. Preflight requires the retained AB snapshot/disassembly and installed Capstone; build uses the existing local toolchain. Audit retained evidence before a later build changes the executable hash. The completed enabled invocation is not repeated automatically.

**Stopped after Task AC. No successor POP, answer completion, count/phase progression, score/history/save/menu integration, optimization or Task AD.**
