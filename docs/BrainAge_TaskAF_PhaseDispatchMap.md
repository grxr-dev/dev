# Task AF - read-only map of pending phase path

**FULL PASS. Static analysis only: zero guest instructions executed in AF.** The exact AE state selects the phase-halfword-1 arm of `02026218`. Its first non-stack store is `0202624C / E5840034`, writing `000000DA` to exercise `+34`, already `000000DA`. Recommend the smallest AG slice: **start 02026B90; halt before 0202624C**, after eight original instructions including the outer BL. No object store or inner call is needed to prove dispatch selection.

[Machine-readable result](BrainAge_TaskAF_Result.json); [read-only verifier](../tools/task_af/analyze.py).

## Provenance and scope

Authoritative AE commit: `6a43d5bfa4c85773b0f986b9d73944ab5e01700e`; AD: `a8502da4a156cf4cee756ee85afc2e016533bab8`. Branch is `codex/brainage`. Actual repository HEAD at start was `5a37a257d09344df7c992fb8ba9dee9abd6630c1`: two later Inbox commits, with no diff in AE reports/helpers. They and the unrelated untracked Inbox ZIP are preserved. Local ndsrecomp HEAD matches pinned `3a57236bb23d25dcb4caad7d58d733311062ff5e`.

Selected ROM SHA-1 independently verified: `b8a105bacc3234dede8d4465df0869f2b922a0e2`. Capstone decodes the individual instructions, and every reported instruction word is also checked against the preserved AE main-RAM code. The verifier hashes the retained RAM/DTCM against AE JSON, checks complete AE CPU state, and hashes its source inputs before/after. AE, AD and relevant Z-AA-AB-AC field facts agree; no semantic contradiction was found.

Evidence is **static exact-ROM analysis anchored in forced Tier-3 AE evidence**, not a new Tier-3 run or compiled parity. No runner, replay, scheduler, generated C, ROM, checkpoint or save was modified. AF only creates ROM-free reports and a read-only verifier. Initial sandbox process setup failed; approved escalated local commands supplied file access. No broad recognition/publication experiment was run.

## Exact entry ABI and caller

At AE stop `02026B90`, all values below are hexadecimal:

| Registers | Values |
|---|---|
| r0-r3 | 020E9A00, 00000001, 00000004, 00000000 |
| r4-r7 | 00000003, 00000000, 00000072, 00000000 |
| r8-r12 | 020E9A00, 00000000, 00000000, 00000000, 00000000 |
| SP / LR / PC | 027E3B34 / 00000000 / 02026B90 |
| NZCV / T / mode / I / F | 1/0/0/0 / 0 / 31 decimal (System) / 0 / 0 |

`MOV r0,r8` already executed. r0 points to the previously audited exercise object at `020E9A00` (audited extent C34 bytes), not the separate manager or slot. A source-language structure type is not established. The callee immediately copies r0 to r4; the outer prefix reads no residual r1-r3 arguments. They remain 1/4/0, without invented ABI meanings.

`02026B90 / EBFFFDA0 BL 02026218` would set LR=02026B94, PC=02026218 and leave SP/flags/other registers unchanged. No stack arguments are consumed by the mapped prefix. The callee's `PUSH {r4,lr}` would move SP to 027E3B2C and write:

| DTCM address | Preserved AE word | Predicted pushed word |
|---|---|---|
| 027E3B2C | 00000072 | 00000003 (r4) |
| 027E3B30 | 02026988 | 02026B94 (new LR) |

These eight bytes are released stack storage from the preceding call; this is stack scratch, not a gameplay-field write. Three bytes would differ. AF does not perform the push.

Immediately after a hypothetical full return, caller `02026B94 / E28DD00C` adds C to SP, then `02026B98 / E8BD83F0` pops r4-r9 and PC. Thus the caller expects its stack/callee-saved context restored and does not test the returned r0 before its own return. This is static caller context only, not proof that the unbounded remainder returns safely. Decoding stops at this POP; subsequent literal data is not fallthrough code.

## Field cross-check

Offsets below are hexadecimal relative to 020E9A00. Values are decimal except where marked.

| Offset / address | Width | AE value | Established mechanical use |
|---|---|---|---|
| +10 / 020E9A10 | 2, signed load | 1 | Phase discriminator; preceding AE LDRSH/CMP 2/BNE and current jump-table index |
| +20 / 020E9A20 | 4 | 1 | Result delay; Z established countdown use, AA set it to 1 |
| +504 / 020E9F04 | 4 | 1 | Result flag; AB set it to 1 |
| +44 / 020E9A44 | 4 | 1 | Correct count; no increment in the mapped path |
| +34 / 020E9A34 | 4 | DA hex | Phase-1 arm assigns DA; inner helper loads it into r6. Broader meaning unknown |
| +1C / 020E9A1C | 4 | 0 | Inner helper zero test; no semantic name assigned |
| +3C / 020E9A3C | 4 | 20 | Signed comparison bound in inner helper |
| +40 / 020E9A40 | 4 | 1 | Signed comparison input and scaled index; not conflated with correct count +44 |
| +58 / 020E9A58 | 4 | 11 | Selected element at +54 + 4*(+40), compared with 9 |
| +4C / 020E9A4C | 4 | 4 | Prior expected answer |
| +51C / 020E9F1C | 4 | 255 | Prior later-outcome field; not touched here |
| +7C4 / 020EA1C4 | 4 | 1 | Nested subobject +254; first proven value-changing object store below |

Z established later result-delay expiration leading to +44 increment and +10=2, through a different caller path. Nothing here reclassifies +40 as correct count or +34 as score/timing. Score/history/save field offsets remain unproven.

## Exact outer path

| PC / opcode | Instruction / expected effect |
|---|---|
| 02026B90 / EBFFFDA0 | BL 02026218; creates LR=02026B94 |
| 02026218 / E92D4010 | PUSH {r4,lr}; stack-only writes above |
| 0202621C / E1A04000 | MOV r4,r0; r4=020E9A00 |
| 02026220 / E1D401F0 | LDRSH r0,[r4,#10]; sign-extends halfword 1 |
| 02026224 / E3500005 | CMP r0,#5; 1-5 gives NZCV=1/0/0/0 |
| 02026228 / 908FF100 | ADDLS pc,pc,r0,LSL #2; LS true (C=0 or Z=1). Architectural PC operand is 02026230; plus 4 selects 02026234 |
| 02026234 / EA000003 | Unconditional B 02026248 |
| 02026248 / E3A000DA | MOV r0,#DA; no flag update |
| **0202624C / E5840034** | **STR r0,[r4,#34]; proposed pre-dispatch stop** |
| 02026250 / E1A00004 | MOV r0,r4; only relevant if preceding store separately allowed |
| 02026254 / EBFFFF47 | BL 02025F78; r0-r3=020E9A00/1/4/0, LR would become 02026258 |

The conditional PC addition uses an unsigned LS test after a signed halfword load; it is not merely a test for equality to phase 1. Values outside unsigned 0..5 take fallback 0202622C -> 02026258; slot zero at 02026230 also branches to 02026258; slots 2..5 branch to 02026250. Only the actual slot 1 passes through 02026248/24C. No alternate path executes or influences this state.

## First actions and narrow inner-call proof

The earliest memory write is the stack PUSH at 02026218. The first **object** write is `0202624C / E5840034`: AL, immediate positive offset, word store, no writeback; base r4=020E9A00, offset 34, effective address 020E9A34, source r0=000000DA. Before/after both DA, so zero changed bytes are predicted. Classification: **exercise-object assignment with unknown semantic role, idempotent in this exact state**. It is neither proven gameplay-neutral bookkeeping nor a mapped result/count/phase/score/history field. As an aligned ordinary-RAM store, this exact one instruction is mechanically safe to bound, with clean successor 02026250; including it is unnecessary for the preferred AG proof.

Because that store is idempotent, a narrow static inspection also establishes the first value-changing object write reachable through the next call. This does not authorize either call or decompile their remainder:

| PC / opcode | Exact inner-prefix behavior |
|---|---|
| 02025F78 E92D41F0; 02025F7C E24DD008 | PUSH r4-r8,lr; reserve 8 bytes; stack scratch only |
| 02025F80 E1A07000; 02025F84 E5971040; 02025F88 E597001C; 02025F8C E2415001 | r7=exercise; r1=+40=1; r0=+1C=0; r5=0 |
| 02025F90 E3500000; 02025F94 E5976034; 02025F98 0A00000C | CMP 0,0 (NZCV=0/1/1/0), load r6=DA, BEQ taken to 02025FD0. Skips +1C decrement/store and intervening calls |
| 02025FD0 E5971040; 02025FD4 E597003C; 02025FD8 E1510000; 02025FDC AA000019 | Compare signed 1 vs 20 (NZCV=1/0/0/0); BGE 02026048 not taken |
| 02025FE0 E0871101; 02025FE4 E5910054; 02025FE8 E3500009; 02025FEC CA000002 | r1=exercise+4; load +58=11; CMP 11,9 (NZCV=0/0/1/0); BGT taken to 02025FFC; skips second element test |
| 02025FFC E3A01000; 02026000 E1A02001; 02026004 E2870E57; 02026008 E3A0301F | Prepare r0-r3=020E9F70/0/0/1F |
| 0202600C / EB0106F0 | BL 02067BD4; LR would be 02026010 |
| 02067BD4 E92D4010; 02067BD8 E1A04000 | PUSH r4,lr; MOV r4,r0 |
| **02067BDC / E5842254** | **STR r2,[r4,#254]: word at 020EA1C4 (exercise+7C4), 1 -> 0** |

The last store is the first proven non-stack value change, classified **unknown subobject state**. No result/count/phase/score/progression/history label is proven for it. There are no intervening object writes other than the idempotent +34 assignment, no earlier external calls, and no MMIO in these exact prefixes. Neither inner routine's remaining effects are bounded. No claim that fully dispatching 02025F78 is safe follows from this first-write proof.

## Task AG recommendation and limits

Authorize only a separately implemented, fail-closed exact-prefix experiment from **02026B90 to 0202624C before dispatch**. Eight instructions would prove original BL linkage, the real stack push, signed phase read, unsigned table guard, selected table slot and DA store operand. Expected stop: r0=DA, r4=020E9A00, SP=027E3B2C, LR=02026B94, PC=0202624C; all other registers unchanged from AE; NZCV remains 1/0/0/0. ARM9 ordinal would increase by eight; no cycle prediction is made.

**AG may safely dispatch the outer BL only under this bounded authorization**, validating AE state/code/fields and halting before the store. The two stack words must be audited, rather than claiming DTCM is unchanged. No score/count/phase/progression/history/save effect occurs before this stop: only stack storage changes. Main RAM and mapped fields must remain identical. Require no unexpected guest instructions, MMIO, save request or Flash commit. Forbid the store itself in the preferred experiment, every inner call, full callee return, gameplay continuation, and framework/runtime changes.

If separately requested, executing exactly the idempotent store would permit a nine-instruction slice stopping **02026250**, after the first object write and before operand preparation/inner BL. It should still audit the write despite zero changed bytes. AF recommends the smaller eight-instruction experiment; neither variant is started here.

## Validation

`python tools/task_af/analyze.py --export` passed exact ROM/RAM instruction checks, complete AE state and field checks, branch target arithmetic, RAM/DTCM/save/checkpoint hashes, and source-input before/after hash equality. `python tools/task_af/analyze.py` repeats read-only checks without exporting. JSON includes full register arrays, individual decoded facts, hash provenance, predicted stack words and both store descriptions. No emulator, guest interpreter or replay is invoked by the helper.

These are static predictions for one preserved 11 - 7 / recognized-4 context. Dynamic guard behavior, scheduler effects, and compiled parity remain untested in AF. AE's reported ARM7 cycle accounting is unchanged historical evidence and was not investigated.

**Stop after Task AF. Pending BL has not executed. Task AG has not begun.**
