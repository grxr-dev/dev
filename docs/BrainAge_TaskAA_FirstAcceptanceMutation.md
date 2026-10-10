# Task AA ? first original acceptance mutation

**FULL PASS, first store only, forced Tier-3.** The exact Task Z causal SDL input reached the same correct predicate. Original instructions `02025734` and `02025738` executed. The disposable process halted with next guest PC **0202573C**, before that second store. The answer was not completed and gameplay was not resumed.

Starting milestone: Task Z commit `343a3daf41f05ab5ff14ea05124da2045cafe6cb`, branch `codex/brainage`. Exact ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Derived evidence: [Task AA result](BrainAge_TaskAA_Result.json).

## Causal reproduction and boundary

One fresh disabled control and **one fresh authoritative enabled invocation** were run. Both exited 0 without forced cleanup. Source checkpoint/save stayed immutable. Task Z evidence was reused for comparison; its guest experiment was not rerun.

The unchanged frozen input SHA-256 is `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`. Its committed definition contains two strokes: `(190,110),(156,91),(121,65),(121,98),(121,130)` and `(173,114),(132,114),(75,114)`. These are the four button edges plus six motion events, not four separately invented glyphs. All ten events passed through `SDL_PushEvent -> normal frontend mapping -> nds_set_touch -> native owner`. Recognition returned 2 then 4, secondary 0, metrics 500/249, countdown 41/1. No direct candidate injection or custom guest touch delivery occurred.

Original publication and the original correctness consumer each entered once. The first 42 pre-dispatch observations match retained Task Z exactly: all registers, flags, PCs, opcodes and instruction ordinals. The authorized extension is:

| Boundary | Observed behavior |
|---|---|
| `02025728 E1510005` | Original comparison of submitted 4 and expected units 4 |
| `0202572C 13A03001` | NE predicate fails; mismatch remains zero |
| `02025730 E3530000` | Final mismatch comparison selects EQ |
| `02025734 03A01001` | MOVEQ executes; r1 changes 4 to 1 |
| `02025738 05801020` | STREQ executes exactly once; `[020E9A20]` changes 0 to 1 |
| **`0202573C 05801504`** | **Read-only terminal observation; instruction is not dispatched** |

At terminal observation: r0=`020E9A00`, r1=1, r2=4, r3=0, r4=10, r5=4, r12=0, SP=`027E3B04`, LR=0, NZCV=0/1/1/0, T=0, System mode 31, I=F=0.

## Why the forbidden instruction could not execute

The opt-in AA hook precedes the interpreter instruction-count/fetch/step dispatch site. Its fixed allowlist contains 44 observations but only 43 dispatchable positions. `dispatches()` rejects `0202573C` at every index. At index 43 the hook validates the completed first store, records state, calls terminal halt, returns 2, synchronizes CPU state and preserves interpreter unwind; the SDL terminal exit then closes the process. Any wrong PC, ordinal, predicate, repeated entry, external/downstream call or unsupported mutation fails closed before dispatch. No synthetic guest return or counter restoration is used.

The measured ARM9 decision ordinal advances 281097834 -> 281097877 (**43**, two more than Z), and cycles advance by 90. ARM7 ordinal/cycles stay fixed. The terminal PC is an observation, not evidence of executing its opcode. The first-store-before snapshot and terminal snapshot isolate the store itself; result flag stays zero.

## Auditable state differences

| Field/region | Before -> immediately after first store |
|---|---|
| Result delay +20 | **0 -> 1** |
| Result flag +504 | **0 -> 0** |
| Correct count +44 | 1 -> 1 |
| Phase +10 | 1 -> 1 |
| Expected +4C | 4 -> 4 |
| Input status +38 | 0 -> 0 |
| Submitted tens +50C / later outcome +51C | 255 -> 255 |
| Manager / active slot | Byte-identical across correctness |
| All 4 MiB main RAM across the single store | Exactly one changed byte: `020E9A20`, 0 -> 1 |
| Entire 16 KiB DTCM across the single store | Byte-identical |

Across the whole decision interval, main RAM has only two changed bytes: allowed result-delay byte at `020E9A20`, plus the already-proven submitted-units staging byte at `020E9F14` (FF -> 04). DTCM has exactly the same 13 changed bytes as Z, reconstructed from the two PUSH writes, with no additional stack changes from the extension. Full exercise audit permits only these two field bytes; no other RAM changes or manager/slot changes are hidden.

Score, progression and history are bounded by exhaustive main-RAM comparison and the exact entry path; no downstream acceptance/progression/history/save routine entered. No independent undocumented offsets are assigned to those concepts. Guest video, scene 11/11/11, touch deliveries and presentation count remain unchanged across correctness. Private recognition had already torn down with main RAM/CPU/counters unchanged and no stale touch/presentation ownership.

Save snapshots before/after, source save and disposable on-disk save are byte-identical, SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`. Logical requests **0**, Flash commits **0**, changed save bytes **0**, dirty=false.

## Evidence and tooling

`tools/task_aa/` narrowly extends Task Z's fixed diagnostic/install/driver and offline audit. Task Z files and production host/service/adapter/policy are unchanged. No arbitrary guest-call API, ROM patch or hand-edited generated ROM-derived C was introduced. Runner SHA-256: `128c27a0c77e173d386b491e87b1907f02b9c0ecef33e6f51826c82eef396397`.

Focused checks passed: AA boundary negative tests including second-store rejection, Task Z prefix/guard, existing publication policy, unchanged production-source checks, pre-dispatch ordering and full offline SDL/state/save audit. The disabled control has no input, recognition, publication, correctness, RAM change or save activity. Existing compiler warnings in historical Task S code were unchanged.

Raw checkpoints, RAM/Flash snapshots, generated runner, window captures and logs remain ignored under `local/task-aa/{disabled-001,session-001}` and `build/`. Only ROM-free source/tests, derived facts and this report are committed. Evidence is **forced Tier-3 for one exact context**, with no compiled acceptance parity or general answer-entry claim. Hold presentation count differs by one from Z due to host timing; the decision state/trace is otherwise identical through Z's stop.

Offline reproduction of this completed evidence:

```powershell
python tools/task_aa/check.py
python tools/task_aa/analyze.py --out local/task-aa/session-001 --disabled local/task-aa/disabled-001 --export docs/BrainAge_TaskAA_Result.json
```

For a separately authorized fresh disposable reproduction, build first, then check, use new output directories, and analyze those directories:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_aa/build.ps1
python tools/task_aa/check.py
python tools/task_aa/run.py --out local/task-aa/disabled-FRESH --disabled --port 19901
python tools/task_aa/run.py --out local/task-aa/session-FRESH --port 19902
python tools/task_aa/analyze.py --out local/task-aa/session-FRESH --disabled local/task-aa/disabled-FRESH --export docs/BrainAge_TaskAA_Result.json
```

The driver reuses the project's selected exact ROM/BIOS/generated-runner arguments and immutable Task Z checkpoint. Rebuilding changes the runner hash, so audit this retained run before a later rebuild. The completed enabled invocation is not repeated automatically.

**Task AA stops here. No second store, full acceptance, count/phase progression, history/save/menu integration, optimization or Task AB.**
