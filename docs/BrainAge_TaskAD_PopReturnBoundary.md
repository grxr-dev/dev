# Task AD - one POP/return instruction beyond Task AC

**FULL PASS.** One fresh frozen real-SDL replay reached the exact Task AC stop. After independent decode and live stack validation, **02025744 / 08BD8030** executed once. The disposable process halted at **02025830 before any target instruction dispatch**. Its `E8BD8010` POP did not execute. Gameplay was not resumed and the answer was not completed.

Predecessor: Task AC `ab430d71d42f7122199f3a35e9922a166972c113`; branch `codex/brainage`. Exact ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. [Machine-readable result](BrainAge_TaskAD_Result.json).

## Identification and stack provenance before execution

The read-only preflight independently decoded the selected exact-ROM bytes with Capstone, cross-checked retained Task Z disassembly, and verified the committed Task AC register state and hashed DTCM/main-RAM snapshots. The derived identification was frozen before the enabled run. Generated ROM-derived C was not edited.

Opcode **08BD8030** is **POPEQ {r4,r5,pc}**, alias **LDMEQIA sp!,{r4,r5,pc}**. EQ executes because Z=1; NZCV=0/1/1/0, System mode 31, T=0. Encoding: P=0, U=1, S=0, W=1, L=1, base r13, register mask 8030. Reads occur in ascending register order; the instruction performs no memory write. S=0 means no SPSR restoration. The even aligned loaded PC retains ARM state. LR is absent from the register list and remains zero.

| DTCM read address | Exact word | Destination |
|---|---|---|
| 027E3B08 | 00000001 | r4 |
| 027E3B0C | 020E9A00 | r5 |
| 027E3B10 | 02025830 | PC |

These are the original comparison helper's saved r4, r5 and LR. The causal trace has `0202582C / EBFFFF99` BL establishing LR=02025830, followed by `02025698 / E92D4030` PUSH {r4,r5,lr}. At that original PUSH, SP=027E3B14 and source values are exactly the three words above. It wrote 027E3B08..027E3B13. Task AC's ADD released the helper's four-byte local reservation; it did not overwrite the saved words. The outer consumer's earlier PUSH at 02025778 has its own unchanged footprint at 027E3B14..027E3B1B. Offline reconstruction accounts for every changed DTCM byte across the entire decision prefix.

Before allowing AD dispatch, the live hook rechecked EQ, opcode/address-mode/register-list/S-bit, SP, r4/r5/LR, all three actual stack words, helper-entry provenance, original BL/PUSH opcodes, and return-site opcode. Any contradiction halts before dispatch.

## Exact architectural effect and stop

| Register | Before -> after AD |
|---|---|
| r4 | 0000000A -> 00000001 |
| r5 | 00000004 -> 020E9A00 |
| SP | 027E3B08 -> 027E3B14 |
| PC | 02025744 -> 02025830 |
| LR | 00000000 -> 00000000 |
| All remaining registers / CPSR | Unchanged |

The return target is an already-entered consumer's caller-side return site. The hook observes that address, but **zero instructions there execute** and no new downstream routine body runs. The target opcode is independently checked as **E8BD8010 / POP {r4,pc}** solely for stop identification; it remains forbidden.

The fixed path has **47 observations / 46 dispatches**. Its first 46 observations exactly match Task AC, including PCs, opcodes, every register, flags and ARM9 instruction ordinals. `dispatches()` rejects the target at every index. The installed hook runs before bank handoff, instruction counting, fetch and Interpreter::step. After the POP, ordinary host return bookkeeping does not dispatch guest caller code; the next loop's terminal hook halts, synchronizes CPU state and preserves unwind. No synthetic guest return, counter restoration or arbitrary guest-call API is introduced.

Immediate ARM9 ordinal **281097879 -> 281097880** proves exactly one extra dispatch; cycles **3416875387 -> 3416875394** reflect the interpreted load/return cost. ARM7 cycles/ordinal stay unchanged. Both fresh processes exit 0 without forced cleanup.

## Replay and immediate state audit

The unchanged input digest is `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`. Stroke 0 is `(190,110),(156,91),(121,65),(121,98),(121,130)`; stroke 1 is `(173,114),(132,114),(75,114)`. All ten events, including four button edges, use SDL_PushEvent -> ordinary coordinate mapping -> nds_set_touch -> native owner. Recognition remains 2 then 4; custom guest deliveries are zero. The isolated recognizer is torn down before original publication/correctness. No input geometry, production service or policy changed.

Immediate pre-AD RAM/DTCM are byte-identical to Task AC's stop. Only host presentation timing varies (161 held frames here, 160 in AC); the guest prefix remains exact.

| State | Immediately before -> after POP |
|---|---|
| Result delay +20 | 1 -> 1 |
| Result flag +504 | 1 -> 1 |
| Correct count +44 | 1 -> 1 |
| Phase +10 | 1 -> 1 |
| Entire 4 MiB main RAM | Zero changed bytes |
| Entire 16 KiB DTCM / stack memory | Zero changed bytes |
| Guest video / touch / scene / native ownership | Unchanged |
| Downstream instructions / effects | Zero |

Main RAM before/after SHA-256: `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9`. DTCM before/after: `e2ab6955f9cfa7e43239c75a004e386609c55a282d291c6a286ea97954e062ff`. POP reads stack words; it does not erase them.

Earlier input/AA/AB mutations remain separate: submitted units FF -> 04, delay 0 -> 1, flag 0 -> 1, and the same 13 changed DTCM bytes from the two original PUSHes. None is new in AD. Manager/slot and other exercise fields remain unchanged. Score/progression/history exclusion follows from the exhaustive immediate RAM/DTCM comparison and exact register-only instruction path; no speculative field offsets are invented.

Save/source/live/disposable Flash stays byte-identical: SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; changed bytes 0, logical requests 0, Flash commits 0, dirty=false. Source checkpoint remains immutable.

## Tests, evidence limits and reproduction

Focused checks pass: POP opcode/list/condition/SP/stack-word negative cases; AC-prefix parity; terminal dispatch rejection at every index; ordinal, repeat, wrong-path and downstream rejection; predecessor AC guard; frozen publication policy; unchanged production host/service/policy files; hook ordering before bank handoff and interpreter dispatch. Disabled control has zero recognition/publication/correctness/input activity and zero RAM/save changes. Offline analysis checks all causal events, exact prefix, register/flag changes, full memory diffs, stack provenance, source/save identity and clean exits. Build passed with only existing historical Task S warnings.

Evidence tier: **forced Tier-3 original ARM interpreter**, one exact 11 - 7 / recognized-4 context. No compiled acceptance parity, full answer completion or later progression claim. Runner SHA-256 `101ccea62692d9a97768822712541a61768087ea09de5001c1ec96aecf8ab2be`.

Only ROM-free tools/task_ad source/tests and derived report/JSON are committed. ROM, disassembly, code snapshots, saves, checkpoints, RAM images, captures and runner remain local/ignored. Earlier task artifacts and production code are unchanged.

Audit completed local evidence before rebuilding changes the runner hash:

```powershell
python tools/task_ad/preflight.py
python tools/task_ad/check.py
python tools/task_ad/analyze.py --out local/task-ad/session-001 --disabled local/task-ad/disabled-001 --export docs/BrainAge_TaskAD_Result.json
```

For a separately authorized fresh disposable reproduction:

```powershell
python tools/task_ad/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ad/build.ps1
python tools/task_ad/check.py
python tools/task_ad/run.py --out local/task-ad/disabled-FRESH --disabled --port 19931
python tools/task_ad/run.py --out local/task-ad/session-FRESH --port 19932
python tools/task_ad/analyze.py --out local/task-ad/session-FRESH --disabled local/task-ad/disabled-FRESH --export docs/BrainAge_TaskAD_Result.json
```

The driver reuses the existing selected ROM/BIOS arguments and immutable Task G checkpoint. Preflight needs retained AC snapshots/trace, Task Z disassembly and Capstone; build uses the existing local toolchain. The completed enabled run is not repeated automatically.

**Stopped after Task AD. No instruction at 02025830, gameplay resume, later progression, scoring/history/save/menu integration, optimization or Task AE.**
