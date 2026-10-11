# Task AJ - exact inner-helper static map

**FULL PASS.** Static analysis only; zero guest instructions dispatched. AF's first-change claim is verified with no divergence. Recommend a separately authorized AK prefix of **25 instructions**, starting **0x02026254** and stopping **before 0x02067BDC**. AK has not begun.

[Result JSON](BrainAge_TaskAJ_Result.json) and [read-only verifier](../tools/task_aj/analyze.py).

## Provenance and ABI

Authoritative AI `5e086cb667a87d41eda1aec016e6418a57f64356`, AH `2b846d5ddeb751c59f02caa1aacd227d016a9b24`, AF `63ff0c59f995fe9e2df57248ef261d1f4c8c6819`; branch `codex/brainage`. Initial HEAD was AI. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Committed reports/helpers match those commits. ROM instruction words also match retained AI main RAM. AI CPU is cross-checked against its retained audit log; complete RAM/DTCM/save and source checkpoint hashes match. All inspected input hashes are unchanged after analysis. Unrelated `jarvis-inbox-v1.zip` is preserved.

AI pre-call r0-r12 (hex): `020E9A00, 1, 4, 0, 020E9A00, 0, 72, 0, 020E9A00, 0, 0, 0, 0`. SP=`027E3B2C`, LR=`02026B94`, PC=`02026254`; NZCV=`1/0/0/0`, T=0, System mode=31, I=F=0.

`02026254 / EBFFFF47 / BL 02025F78` creates LR=`02026258`, changes PC to `02025F78`, and leaves SP, flags and r0-r12 unchanged. r0 is the exercise pointer consumed by MOV r7,r0. Incoming r1/r2/r3 are incidental on this exact prefix: each is overwritten before use. No stack argument is read. This is a machine-level ABI observation, not a recovered source signature or whole-function liveness claim. r12=0 is untouched. Saved LR=02026B94 remains in the existing caller frame at 027E3B30; BL itself performs no stack write.

Immediately after a hypothetical return: `02026258 / E5940004 / LDR r0,[r4,#4]`, then `0202625C / E3500000 / CMP r0,#0`. Thus returned r0 is overwritten before comparison; the caller expects preserved r4. The remainder and actual return are outside this proof.

## Exact path

Every listed instruction is AL except the three named conditional branches. Unlisted registers and flags are unchanged; PC advances by four except at taken branches/calls. LR changes only at the two BLs; SP changes only at the two PUSHes and SUB. All object loads are aligned 32-bit ordinary main-RAM reads. No unknown access or MMIO occurs.

| Index | PC / opcode | Decode | Class and exact effect |
|---|---|---|---|
| 0 | 0x02026254 / 0xEBFFFF47 | bl #0x2025f78 | call: LR=02026258; SP unchanged; target 02025F78 |
| 1 | 0x02025F78 / 0xE92D41F0 | push {r4, r5, r6, r7, r8, lr} | stack write: PUSH r4-r8,LR; SP 027E3B2C -> 027E3B14; six words |
| 2 | 0x02025F7C / 0xE24DD008 | sub sp, sp, #8 | register: SP 027E3B14 -> 027E3B0C; reserve 8 bytes, no write |
| 3 | 0x02025F80 / 0xE1A07000 | mov r7, r0 | register: r7=r0=020E9A00 |
| 4 | 0x02025F84 / 0xE5971040 | ldr r1, [r7, #0x40] | object read: [020E9A40]=1 -> r1 |
| 5 | 0x02025F88 / 0xE597001C | ldr r0, [r7, #0x1c] | object read: [020E9A1C]=0 -> r0 |
| 6 | 0x02025F8C / 0xE2415001 | sub r5, r1, #1 | register: r5=1-1=0; flags unchanged |
| 7 | 0x02025F90 / 0xE3500000 | cmp r0, #0 | flags: CMP 0,0 -> NZCV 0/1/1/0 |
| 8 | 0x02025F94 / 0xE5976034 | ldr r6, [r7, #0x34] | object read: [020E9A34]=DA -> r6; flags unchanged |
| 9 | 0x02025F98 / 0x0A00000C | beq #0x2025fd0 | branch: EQ true (Z=1); taken 02025FD0 |
| 10 | 0x02025FD0 / 0xE5971040 | ldr r1, [r7, #0x40] | object read: [020E9A40]=1 -> r1 |
| 11 | 0x02025FD4 / 0xE597003C | ldr r0, [r7, #0x3c] | object read: [020E9A3C]=20 decimal -> r0 |
| 12 | 0x02025FD8 / 0xE1510000 | cmp r1, r0 | flags: CMP 1,20 -> NZCV 1/0/0/0 |
| 13 | 0x02025FDC / 0xAA000019 | bge #0x2026048 | branch: GE false (N!=V); not taken 02026048; next 02025FE0 |
| 14 | 0x02025FE0 / 0xE0871101 | add r1, r7, r1, lsl #2 | register: r1=020E9A00+(1<<2)=020E9A04 |
| 15 | 0x02025FE4 / 0xE5910054 | ldr r0, [r1, #0x54] | object read: [020E9A04+54]=[020E9A58]=11 decimal -> r0 |
| 16 | 0x02025FE8 / 0xE3500009 | cmp r0, #9 | flags: CMP 11,9 -> NZCV 0/0/1/0 |
| 17 | 0x02025FEC / 0xCA000002 | bgt #0x2025ffc | branch: GT true (Z=0,N=V); taken 02025FFC |
| 18 | 0x02025FFC / 0xE3A01000 | mov r1, #0 | register: r1=0 |
| 19 | 0x02026000 / 0xE1A02001 | mov r2, r1 | register: r2=r1=0 |
| 20 | 0x02026004 / 0xE2870E57 | add r0, r7, #0x570 | register: r0=020E9A00+570=020E9F70 |
| 21 | 0x02026008 / 0xE3A0301F | mov r3, #0x1f | register: r3=1F |
| 22 | 0x0202600C / 0xEB0106F0 | bl #0x2067bd4 | call: target 02067BD4; LR=02026010; SP=027E3B0C |
| 23 | 0x02067BD4 / 0xE92D4010 | push {r4, lr} | stack write: PUSH r4,LR; SP 027E3B0C -> 027E3B04; two words |
| 24 | 0x02067BD8 / 0xE1A04000 | mov r4, r0 | register: r4=r0=020E9F70 |
| 25 | 0x02067BDC / 0xE5842254 | str r2, [r4, #0x254] | FORBIDDEN object write: STR r2=0 to [r4+254]=020EA1C4; before=1; STOP BEFORE DISPATCH |

+40=1 selects index 1 and r5=0; +1C=0 takes BEQ, skipping the nonzero arm entirely. +34=DA is loaded into r6. Signed 1<20 from +40/+3C rejects BGE. The indexed load is +54+4*1=+58=11; signed 11>9 takes BGT. All three predicates and branch immediates were checked independently of AF. No earlier nested call or object/global store lies on this selected path.

## Write and call firewall

The first PUSH writes six words at 027E3B14..027E3B2B. SUB reserves 027E3B0C..027E3B13 without writing it; its retained words remain 020E9A00 and 02025830. The nested PUSH writes two words at 027E3B04..027E3B0B. All lie below AI SP, in released ordinary DTCM stack storage, newly allocated as saved-register frames/local scratch. Existing active caller storage at/above 027E3B2C is untouched. No red-zone or incoming stack data is read by this prefix.

| Write PC | DTCM word address | Source | AI before | Predicted after | Changed bytes |
|---|---|---|---|---|---|
| 0x02025F78 | 0x027E3B14 | r4 | 0x00000001 | 0x020E9A00 | 4 |
| 0x02025F78 | 0x027E3B18 | r5 | 0x020266B8 | 0x00000000 | 4 |
| 0x02025F78 | 0x027E3B1C | r6 | 0x00000000 | 0x00000072 | 1 |
| 0x02025F78 | 0x027E3B20 | r7 | 0x02067524 | 0x00000000 | 4 |
| 0x02025F78 | 0x027E3B24 | r8 | 0x00000003 | 0x020E9A00 | 4 |
| 0x02025F78 | 0x027E3B28 | lr | 0x00000000 | 0x02026258 | 4 |
| 0x02067BD4 | 0x027E3B04 | r4 | 0x00000000 | 0x020E9A00 | 3 |
| 0x02067BD4 | 0x027E3B08 | lr | 0x00000001 | 0x02026010 | 4 |

These are 8 architectural word writes / 32 written bytes, with **28 changed bytes**, not 32 changed bytes. The JSON records every differing byte and predicted DTCM SHA-256 `1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716`. All eight saved words change value; no object/global write, even idempotent, precedes the stop. AH's earlier +34 store is outside the AK-only extension.

At `0202600C / EB0106F0`, the first nested BL targets `02067BD4`, with r0-r3=`020E9F70 / 0 / 0 / 1F`; SP=`027E3B0C`, incoming LR=`02026258`, outgoing LR=`02026010`. Its bounded prefix is exactly `02067BD4 / E92D4010 PUSH {r4,lr}` and `02067BD8 / E1A04000 MOV r4,r0`. Saved r4 is still `020E9A00` at the PUSH. Both calls are statically bounded to this stop; neither full body is claimed safe.

First object/global mutation: **02067BDC / E5842254 / STR r2,[r4,#0x254]**, AL, word, positive immediate, no writeback. r4=`020E9F70`; effective address=`020EA1C4`=exercise+7C4; source r2=0; retained before=1, predicted after=0 (one byte differs). Its semantic role remains unknown. AF's path, arguments, prefix opcodes, address and 1->0 claim are all verified. This store was decoded but never dispatched.

## Fail-closed AK recommendation

Start at the exact AI pre-dispatch stop **02026254**. Permit exactly the ordered 25-instruction prefix at indices 0..24 above, including both BLs and the condition-failed BGE as a dispatched instruction. Observation 25 is terminal-only at **02067BDC**, before fetch/dispatch, bank handoff or instruction increment. Expected ARM9 ordinal is **281097924** (+25); no cycle estimate is made.

Expected terminal r0-r12 (hex): `020E9F70, 0, 0, 1F, 020E9F70, 0, DA, 020E9A00, 020E9A00, 0, 0, 0, 0`. SP=`027E3B04`, LR=`02026010`, PC=`02067BDC`; NZCV=`0/0/1/0`; T=0, System mode=31, I=F=0. No full return is allowed.

Require exact AI CPU, complete RAM/DTCM/save hashes, ROM identity, instruction words, ordinal and all mapped field values before arming. Check the ordered PC/opcode/register/flag path; reject wrong/repeated/skipped entries before dispatch. Permit only the eight listed DTCM word stores with exact PC/address/width/value/order. Permit only instruction fetches and listed object reads; reject unknown/MMIO reads and any additional write. Stop before the STR regardless of operand equality; forbid all later instructions, full helper returns, gameplay continuation and save/Flash requests. Audit actual write events separately from byte diffs. These are requirements for future AK implementation, not guards implemented or dynamically tested by AJ.

Expected full main-RAM/object diff: **zero bytes**, hash `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9`. Expected save diff zero; logical requests/Flash commits zero. Only the listed DTCM bytes may differ. All mapped fields remain unchanged: +10=1, +1C=0, +20=1, +34=DA hex, +38=0, +3C=20, +40=1, +44=1, +4C=4, +58=11, +504=1, +50C=255, +514=4, +51C=255, +7C4=1 (other values decimal). This does not assign semantics to unknown fields. Specifically +7C4 remains 1 because its store is forbidden.

## Validation and limits

`python tools/task_aj/analyze.py --export` verifies and exports only these two ROM-free reports; omit `--export` for read-only checking. It uses explicit static instruction facts and arithmetic obligations, Capstone decoding, immutable retained images and an in-memory stack-byte projection for diff arithmetic. It never invokes an emulator, interpreter, replay, build, guest scheduler or pending call, and never writes a guest image. Each source input is hashed before/after. Individual opcode facts are analytical evidence, not a ROM/code-image artifact.

Evidence tier: static exact-ROM analysis anchored in retained forced Tier-3 original-interpreter AI evidence. No new dynamic evidence, compiled parity, full-routine safety, scheduler or cycle claim. Prediction is conditional on the exact AI state and a future fail-closed runtime gate. Initial sandbox process setup failed; approved escalated file-access commands succeeded. No authoritative input or runtime source was changed.

**Stopped after AJ. Pending BL not executed; AK not started.**
