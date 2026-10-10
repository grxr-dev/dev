# Task Z: guarded original correctness decision

**FULL PASS for one bounded correct-decision experiment, forced Tier-3. The answer was not accepted.** The original consumer reached a proven correct predicate, and execution stopped at **0x02025734**, before the first acceptance store at **0x02025738**. Correct count, phase, result delay, result flag, progression, history and save did not change. The exercise has one explained input byte change; it is not byte-identical.

Predecessor: `256c4412f5052ddd17ad307f5c6c66a65515653f` (Task Y); Task X: `b08cb211687368e4ca9f089f7dfb3f71a5c8b1d6`. ROM SHA-1: `b8a105bacc3234dede8d4465df0869f2b922a0e2`. Framework baseline: `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Machine-readable evidence: [Task Z result](BrainAge_TaskZ_Result.json).

## Evidence provenance

The requested fresh Astra Medium thread discovered existing untracked Task Z source drafts and completed ignored evidence: `local/task-z/static-001`, `disabled-001`, and `session-001`. These were preserved and independently audited, not silently presented as a new execution. **No second authoritative handwriting/correctness invocation was run.** There is exactly one retained enabled invocation and one retained disabled control. Their processes exited 0 without forced cleanup.

The static files were created at 11:26:06 local time on 2026-10-10, before the enabled run at 11:30:33-11:30:40. Fresh read-only exact-ROM regeneration into `static-verified-002` matches every original static range/disassembly file. The existing executable SHA-256 is `f3ccf4cd4c377d0f345d1b943e47f134ecedd6d475da43038f50b203b62b4e28`, identical to both session manifests. Installed diagnostic sources match the retained draft after UTF-8 BOM and newline normalization, exactly as `install.py` loads them. The sole apparent source mismatch was the include file's BOM; no functional difference existed. Current build verification passes. This audit cannot reconstruct an absent historical compiler transcript; the retained executable, installed sources, recorded instruction opcodes and regenerated ROM map agree.

Fresh work added the offline byte-level analyzer, this report and derived result, and reran focused unit/service regressions. The disabled result and authoritative guest trace are retained evidence, not fresh runs. The original Task Y publication evidence was independently re-audited and still passes. Unrelated `jarvis-inbox-v1.zip` was untouched.

## Static map before the decision

The bounded map covers `02025698..0202583B`, caller `02026510..0202670F`, and the small downstream helper `02026BE4..02026C07`. Literal pools at `02025770/74` and `02025834/38` contain `66666667` and `0000000A`; they are data, not executed disassembly.

| PC / opcode | Mechanical behavior on this exact context |
|---|---|
| `020266B4 EBFFFC2F` | Original `BL 02025778`; r0=exercise `020E9A00`, r1=0, r2=recognized 4. |
| `02025778 E92D4010` | Push r4/lr on the existing DTCM stack. |
| `0202577C E3A010FF`; `02025780 E580150C`; `02025784 E5801514` | Set r1=255; reset exercise +50C/+514 to 255. Both already 255. |
| `02025788 E3A01000`; `0202578C E5801020` | Set r1=0; write +20=0, already 0. |
| `02025790 E3520A01`; `02025794 DA000004` | Compare submitted r2 against 4096, take signed LE branch to `020257AC`. |
| `020257AC E5801038` | Write +38=0, already 0. |
| `020257B0 E590104C`; `020257B4 E3510009`; `020257B8 DA000015` | Read expected=4 from +4C, compare to 9, take LE to `02025814`. |
| `02025814 E352000A` | Compare submitted 4 to 10. GE instructions `02025818..02025824` are condition-failed: no +38 increment or return. |
| `02025828 E5802514` | Store submitted r2=4 at exercise +514. This is input staging before correctness, not an acceptance result. |
| `0202582C EBFFFF99` | Original `BL 02025698`, LR=`02025830`. |
| `02025698 E92D4030`; `0202569C E24DD004` | Push r4/r5/lr; reserve four stack bytes. |
| `020256A0 E5901514`; `020256A4 E3A03000` | Load submitted units into r1=4; initialize mismatch accumulator r3=0. |
| `020256A8 E3510009` | Reject >9 through conditional stack unwind/return at AC/B0; neither executes here. |
| `020256B4 E590204C`; `020256B8 E3520009`; `020256BC DA000011` | Load expected r2=4; take LE to `02025708`, skipping the tens comparison. |
| `02025708..02025724` | Signed multiply by 0x66666667, high-word ASR 2 and sign adjustment compute expected/10; multiply quotient by 10 and subtract from expected. Here quotient=0 and r5=4 (expected units). No writes/calls. |
| `02025728 E1510005` | `CMP r1,r5`: submitted 4 versus expected units 4. NZCV becomes 0/1/1/0. |
| `0202572C 13A03001` | `MOVNE r3,1` is condition-failed, preserving mismatch=0. |
| `02025730 E3530000` | `CMP r3,0`: final correct/incorrect discriminator. NZCV=0/1/1/0 selects EQ. |
| **`02025734 03A01001`** | **Chosen stop, before `MOVEQ r1,1` dispatch. Correct predicate already proven.** |
| **`02025738 05801020`** | **First forbidden acceptance mutation: `STREQ r1,[r0,#20]`, sets `020E9A20` from 0 to 1. Never reached.** |
| `0202573C 05801504` | Following forbidden store sets +504=1. Conditional unwind at 02025740/02025744 returns. |

For the single-digit context the earliest decisive post-comparison boundary is **0202572C**: equality flags and r3=0 already prove no mismatch. The chosen boundary 02025734 additionally observes the original final `CMP r3,0` after the conditional mismatch instruction was skipped. It is still before any acceptance mutation. There is no branch instruction at this final split: ARM conditional execution selects the EQ stores/return. An incorrect comparison sets r3=1 at 72C; final CMP has Z=0, skips EQ acceptance, and falls through to `02025748`, which writes a different delay (1 or 30 according to +4) and +504=0. That wrong path is forbidden by the Task Z exact sequence.

For larger expected values, `020256C0..02025704` also validates/compares staged tens at +50C against expected/10 and sets the same mismatch accumulator. That alternative was statically inspected only; it was not dynamically exercised or generalized into an API.

`02025698` is now mechanically established as the needed comparison helper, rather than an opaque progression entry. Its one bounded entry **before** the authorized decision boundary is necessary to decide correctness; no return from it or execution beyond the boundary is allowed. This refines earlier mapping rather than relaxing the prohibition on downstream progression.

## First acceptance and later mutations

Exercise +20 is mechanically a result delay: `02026580` reads it, `0202658C/590` decrement/store it, and `02026594` loads +504. When the delay expires and +504 is nonzero, the original caller invokes `02026BE4` at **020265D4 (EB000182)**, increments correct count +44 at **020265E4 (E5851044)**, writes +51C=0 at **020265F0 (E585451C)**, and sets phase halfword +10 to 2 at **020265F8 (E1C501B0)**. The latter is the verified semantics of Task Y's tentative accepted-phase name. These are all downstream and unexecuted.

`02026BE4` calls manager-related `020521A0` at 02026BF4, then `02066D58` at 02026C00. Their broader semantics were not needed or invented. Any call outside the exact decision path fails before dispatch. No score/timing result, next problem, exercise completion, history or save path executes. The first store to +20 is forbidden even though it precedes count/phase increments.

The earlier +514 write is not acceptance: `02025828` copies the submitted integer before any comparison, and the static incomplete two-digit path also writes it at `0202580C` before returning without comparison. It is a persistent exercise input field, **not stack/local scratch**. For this experiment it changes one byte from FF to 04; no result flag/delay changes. The equal-value initialization stores to +50C/+514/+20/+38 execute but cause no byte change and do not commit acceptance. This distinction is required for the FULL classification; the exercise is never described as wholly unchanged.

## Firewall and causal input

Task Z is opt-in via `NDS_TASK_Z_OUT` and `NDS_TASK_Z_PUBLICATION=1`; disabled publication stops read-only at the same initial gate. The driver verifies ROM, immutable source checkpoint/save and the frozen Task Y gesture before launch. Runtime additionally requires exact scene 11/11/11 (hex), exercise/manager/slot addresses and full object hashes, original opcodes, code-range hash, problem expected=4, count=1, phase=1, empty idle policy-2 slot and clean ownership.

The fixed gesture SHA-256 remains `88d9a22421816f6e390033f2f2b4c553fd73e6706efd3133d96b6ca35e31dd32`. The two unchanged strokes contain 5+3 points. Ten events are audited through **SDL_PushEvent -> normal frontend mapping -> nds_set_touch -> native capture -> private recognizer**. Actual groups yield **2 then 4**, secondary 0 both times, metrics 500/249, policy countdowns **41 then 1**. The expected value is read only by unchanged title policy, not injected into recognition. Private instruction counts remain 636956 and 1561436; cleanup 13160, success and inactive.

Native ownership is removed and the private service torn down before original publication. Full live RAM and both CPU representations remain identical during isolated recognition; guest touch deliveries do not advance. Only the recognition-derived slot +320 and policy countdown +364 are staged. Original `02052424` expires countdown 1 to 0, and the original caller loads r2=4 at `020266B4`. Publication proof is the same 2 -> 4 chain as Y, not direct injection of 4 into correctness.

The pre-dispatch Task Z interpreter hook starts an exact 42-PC sequence including the terminal PC. It checks ordinal, mode, Thumb state, scene, objects, full RAM, full DTCM and Flash at each decision boundary. A divergent PC, wrong predicate, repeated consumer/helper entry, scheduler advancement, out-of-budget instruction, acceptance store, external call or save address halts before dispatch. Exactly 41 instructions dispatch; the 42nd boundary halts. The 64-instruction cap is additional to the exact sequence. No register RPC, synthetic return, guest patch, generated-C change, counter restoration or normal gameplay resume occurs.

## Decision-state audit

Before the call: PC=020266B4, opcode=EBFFFC2F, r0=020E9A00, r1=0, r2=4, r3=0, SP=027E3B1C, LR=02026690, NZCV=0/0/1/0. Consumer entry is exactly once, r2=4 and LR=020266B8.

At stop: **PC=02025734, opcode=03A01001, r0=020E9A00, r1=4, r2=4, r3=0, r4=10, r5=4, r12=0, SP=027E3B04, LR=0, NZCV=0/1/1/0**, ARM state T=0, mode=31 (System), I=F=0. The multiply instructions legitimately use LR as scratch after its push. The EQ MOV has not executed, so r1 is still 4, not 1.

| Region / field | Before -> safe stop |
|---|---|
| Full exercise, 0xC34 bytes | Exactly one byte changed, +514: FF -> 04 |
| Manager, 0x238 bytes | Identical |
| Active slot, 0x370 bytes | Identical across correctness; published integer remains 4, countdown 0 |
| Correct count +44 / phase +10 / expected +4C | 1 -> 1 / 1 -> 1 / 4 -> 4 |
| Result delay +20 / result flag +504 / input status +38 | 0 -> 0 each |
| Submitted tens +50C / later outcome +51C | 255 -> 255 each |
| All 4 MiB main RAM | Only 020E9F14: FF -> 04 |
| Entire 16 KiB DTCM | 13 changed bytes, all within the two PUSH write ranges |
| Flash / logical requests / commits | Identical / 0 / 0 |

The PUSH footprint is 20 bytes: `027E3B14..027E3B1B` stores r4=1 and return `020266B8`; `027E3B08..027E3B13` stores r4=1, r5=020E9A00 and return `02025830`. The analyzer reconstructs these writes against the full before-DTCM image and requires exact equality to the after image. The separate four-byte SP reservation writes nothing. Net changed ranges are `027E3B08..0B` (4), `027E3B0D..14` (8), and `027E3B18` (1); JSON lists each byte before/after. These 13 bytes are ordinary call-stack scratch, not hidden restored counters.

ARM9 advances 41 instructions / 86 cycles across correctness; ARM7 cycles and instruction ordinal remain fixed. Video digest, scene, guest touch count and presentation count remain fixed. Total pre-publication-to-decision main RAM includes the earlier four slot-integer bytes plus the one submitted-units byte; the correctness before/after audit deliberately begins after publication.

Correctness consumer entries **1**, comparison helper entries **1**, forbidden/tripwire hits **0**, acceptance stores executed **0**, downstream progression/completion/history entries **0**, save entries/requests/commits **0/0/0**. There is no claim of acceptance. The terminal half-evaluated process exits cleanly and cannot resume gameplay.

Source checkpoint SHA-256 remains `3911c3e98f90d77916497fd82e4f7ae49e7ca825273e52a90b66fd05ce2b2f2f`. Source, before/after live snapshots and disposable disk Flash all remain `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`, dirty=false.

## Control, focused checks and reproduction

Retained `disabled-001`: no input events, native recognition, staging, original publication or correctness call; full main RAM identical at the read-only gate; count/phase/result/save unchanged; empty logical/Flash traces; exit 0. The source checkpoint/save match the enabled run and remain immutable.

Fresh `tools/task_z/check.py` passes guard negative tests (wrong path, duplicate entry, acceptance/progression/save PCs, budget and incorrect predicate), Task Y policy, Task X groups/secondary, V/W recognizer/service/isolation/resource contracts, arithmetic/freehand and all four catalog selectors. Exact production host/service/exercise sources match Task X. Historical Task Y analyzer rerun passes 2 -> 4 and r2=4 at 020266B4 with four publication RAM bytes and zero save change. No broad gameplay/performance matrix or second authoritative handwriting run was used.

Offline verification of the retained evidence:

```powershell
python tools/task_z/check.py --rom '../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' --code-snapshot local/task-u/session-003/before-mainram.bin
python tools/task_z/analyze.py --out local/task-z/session-001 --disabled local/task-z/disabled-001 --export docs/BrainAge_TaskZ_Result.json
```

`static_map.py`, `build.ps1`, and `run.py` document the fixed experiment setup; do not repeat the enabled run under the completed one-invocation authorization. The analyzer requires fresh static verification directory `static-verified-002` matching `static-001`. Raw ROM/database/code dumps, saves/checkpoints, screenshots, generated C and binaries remain local/ignored. Committed files are ROM-free helpers/tests and derived reports only.

## Separately authorized next task

Evidence supports designing **Task AA: exactly the first acceptance mutation**, requiring separate authorization. Repeat the same frozen causal input in a new disposable process; stop at this proven decision; allow only `02025734 MOVEQ r1,1` and **`02025738 STREQ r1,[r0,#20]`**; halt **before `0202573C`**. Audit that only result delay +20 becomes 1 beyond the already explained input/stack changes, while +504 remains 0, count/phase remain 1/1 and progression/history/save stay unchanged. Retain the fail-closed exact sequence, disabled control and source immutability. This would be only the first acceptance store, not full acceptance or exercise advancement.

**Task Z ends here. Task AA, score/count mutation, phase/progression, history/save/menu integration and optimization were not begun.**
