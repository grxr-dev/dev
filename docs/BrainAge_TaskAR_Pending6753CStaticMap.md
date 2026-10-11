# Task AR - pending 0206753C static map

**FULL PASS for the safe-boundary map.** Recommend 11 instructions from AQ, stopping at `02067564 / EBFE692A / BL 02001A14` before fetch/accounting/dispatch. The whole 0206753C callee is **not** certified bounded or read-only: its first nested operation reaches MMIO writes and polling. AR performed no guest execution; AS was not started.

AQ/AP/AO commits: `06b1432abaac62be3e4649afe58a70b2d5bb793d`, `f36f1ac432a5946f1b451e2d437176447163df3f`, `3e2ecf215823ad1e5b95a4af830d4ee6026152e0`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Committed reports/helpers match. Retained AQ CPU observations, full images, terminal non-dispatch event, access ledgers and mapped fields were checked. Code/literals match ROM and retained RAM. Inputs were hashed before/after.

AQ entry r0-r12=`020E9F70,00060000,0,1,020E9A00,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B0C`, LR=`02067C58`, PC=`02026044`, NZCV=0000; T/mode/I/F=0/31/0/0, ordinal 281097990. Entry hashes: {"mainram": "84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340", "dtcm": "1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716", "save": "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"}.

Unless specified as counts, addresses, offsets and register values below are hexadecimal. BL creates LR 02026048. The callee pushes r4-r11,LR (36 bytes), SP becomes 027E3AE8, then allocates 48C bytes to SP 027E365C. It saves the object pointer at SP+C. No teardown/return occurs in the permitted prefix. Following a return requires crossing excluded MMIO. All included predicates are AL, all instructions preserve NZCV, all fetches are main RAM; unlisted registers are unchanged. JSON contains full before/after states.

| PC / opcode | Decode | Effect | Data access |
|---|---|---|---|
| 0x02026044 / 0xEB01053C | bl #0x206753c | BL creates LR=02026048; target=0206753C | main RAM instruction fetch only |
| 0x0206753C / 0xE92D4FF0 | push {r4, r5, r6, r7, r8, sb, sl, fp, lr} | Save r4-r11,LR in ascending DTCM words; SP -= 24 hex | DTCM stack writes |
| 0x02067540 / 0xE59FC5A4 | ldr ip, [pc, #0x5a4] | r12=[02067AEC]=48C | main RAM ROM literal |
| 0x02067544 / 0xE04DD00C | sub sp, sp, ip | SP -= r12(48C); allocation writes no memory | main RAM instruction fetch only |
| 0x02067548 / 0xE2804F93 | add r4, r0, #0x24c | r4=r0+24C=exercise+7BC | main RAM instruction fetch only |
| 0x0206754C / 0xE5949014 | ldr sb, [r4, #0x14] | r9=[exercise+7D0]=1000 | main RAM exercise+7D0 |
| 0x02067550 / 0xE5941004 | ldr r1, [r4, #4] | r1=[exercise+7C0]=02132750 | main RAM exercise+7C0 |
| 0x02067554 / 0xE58D000C | str r0, [sp, #0xc] | Save r0 at SP+C=027E3668 (idempotent) | DTCM stack writes |
| 0x02067558 / 0xE1A00009 | mov r0, sb | r0=r9=1000 | main RAM instruction fetch only |
| 0x0206755C / 0xE591A02C | ldr sl, [r1, #0x2c] | r10=[02132750+2C]=020FD00C; unnamed pointee field | main RAM pointee+2C; offset-only |
| 0x02067560 / 0xE5948018 | ldr r8, [r4, #0x18] | r8=[exercise+7D4]=1000 | main RAM exercise+7D4 |

The first meaningful architectural effect is PUSH 0206753C: its first word changes 027E3AE8 from 020EA644 to 020E9A00. This is saved-frame storage, not a gameplay claim. Continue through deterministic prologue/argument loads; stop at the first call with external effects. No unknown effect precedes this bounded value-changing store, so the safe-boundary map is FULL PASS. Whole-callee completion is not established.

| Store PC / opcode | DTCM address | Width / source | Before -> after | Class |
|---|---|---|---|---|
| 0x0206753C / 0xE92D4FF0 | 0x027E3AE8 | 4 / r4 | 0x020EA644 -> 0x020E9A00 | value-changing |
| 0x0206753C / 0xE92D4FF0 | 0x027E3AEC | 4 / r5 | 0x00000000 -> 0x00000000 | idempotent |
| 0x0206753C / 0xE92D4FF0 | 0x027E3AF0 | 4 / r6 | 0x020E9A00 -> 0x000000DA | value-changing |
| 0x0206753C / 0xE92D4FF0 | 0x027E3AF4 | 4 / r7 | 0x00000000 -> 0x020E9A00 | value-changing |
| 0x0206753C / 0xE92D4FF0 | 0x027E3AF8 | 4 / r8 | 0x00000001 -> 0x020E9A00 | value-changing |
| 0x0206753C / 0xE92D4FF0 | 0x027E3AFC | 4 / r9 | 0x020E9A00 -> 0x00000000 | value-changing |
| 0x0206753C / 0xE92D4FF0 | 0x027E3B00 | 4 / r10 | 0x00000072 -> 0x00000000 | value-changing |
| 0x0206753C / 0xE92D4FF0 | 0x027E3B04 | 4 / r11 | 0x020E9A00 -> 0x00000000 | value-changing |
| 0x0206753C / 0xE92D4FF0 | 0x027E3B08 | 4 / LR | 0x02026010 -> 0x02026048 | value-changing |
| 0x02067554 / 0xE58D000C | 0x027E3668 | 4 / r0 | 0x020E9F70 -> 0x020E9F70 | idempotent |

All ten writes are DTCM stack words: eight value-changing, two idempotent. None has an exercise-field name. Frame allocation does not initialize other local bytes. No main-RAM/object/global/save/Flash/MMIO write occurs in the prefix.

| Read PC | Address | Word | Class |
|---|---|---|---|
| 0x02067540 | 0x02067AEC | 0x0000048C | main RAM ROM literal |
| 0x0206754C | 0x020EA1D0 | 0x00001000 | main RAM exercise+7D0 |
| 0x02067550 | 0x020EA1C0 | 0x02132750 | main RAM exercise+7C0 |
| 0x0206755C | 0x0213277C | 0x020FD00C | main RAM pointee+2C; offset-only |
| 0x02067560 | 0x020EA1D4 | 0x00001000 | main RAM exercise+7D4 |

## Excluded calls and returns

At 02067564, r0-r3=`1000,02132750,0,1`, SP=`027E365C`, LR=`02026048`; BL would create LR=`02067568`. The call is not read-only: original code proves unconditional MMIO access. Stop before it, not at an arbitrary point within its prologue.

Static lookahead only: 02001A14 would push LR at 027E3658; 02001A18 subtracts 4 to SP 027E3654. At 02001A1C, BL 02001974 would have the same r0-r3, incoming LR 02067568, created LR 02001A20. That leaf loads literal pointers and issues STRH 02001980 to 04000280 (width 2,r3=1); STR 02001988 to 04000290 (width 4,r12=0); STR 02001994 to 04000294 (width 4,r3=1000); STR 02001998 to 04000298 (width 4,r0=1000); STR 0200199C to 0400029C (width 4,r12=0). These are MMIO. Before-values/device effects are unproven; none is in the AS allowance.

Excluded BX LR 020019A0 would return 02001A20 without changing SP. Register arithmetic leaves r0-r3=`1000,04000298,04000290,1000`, r12=0, LR 02001A20. BL 020019B0 at 02001A20 would create LR 02001A24, SP 027E3654. This leaf reads a halfword at 04000280, ANDS bit 8000, then BNE 020019BC loops to 020019B4 when Z=0. Predicate depends on unobserved MMIO; iteration count and final state are not certified. Later reads 040002A0/A4 are also MMIO. Wrapper ADD SP,#4 and POP PC 02001A24/28 would undo its 8-byte frame and return 02067568 only if polling completes. They are excluded, as is all 0206753C teardown/caller continuation. JSON records each lookahead opcode/decode and checked pointer literal.

## Exact AS recommendation

Sequence: `02026044 -> 0206753C -> 02067540 -> 02067544 -> 02067548 -> 0206754C -> 02067550 -> 02067554 -> 02067558 -> 0206755C -> 02067560`; halt at 02067564 before its BL. Exactly 11 instruction fetches, five data-read words, ten DTCM word writes; ordinal 281098001 predicted. No cycle/scheduler prediction.

Final r0-r12=`1000,02132750,0,1,020EA1BC,0,DA,020E9A00,1000,1000,020FD00C,0,48C`; SP=`027E365C`, LR=`02026048`, PC=`02067564`, NZCV=0000; T/mode/I/F=0/31/0/0. Main RAM/save have zero byte differences. DTCM has exactly 21 changed bytes:

| DTCM byte | Before | After |
|---|---|---|
| 0x027E3AE8 | 44 | 00 |
| 0x027E3AE9 | A6 | 9A |
| 0x027E3AF0 | 00 | DA |
| 0x027E3AF1 | 9A | 00 |
| 0x027E3AF2 | 0E | 00 |
| 0x027E3AF3 | 02 | 00 |
| 0x027E3AF5 | 00 | 9A |
| 0x027E3AF6 | 00 | 0E |
| 0x027E3AF7 | 00 | 02 |
| 0x027E3AF8 | 01 | 00 |
| 0x027E3AF9 | 00 | 9A |
| 0x027E3AFA | 00 | 0E |
| 0x027E3AFB | 00 | 02 |
| 0x027E3AFD | 9A | 00 |
| 0x027E3AFE | 0E | 00 |
| 0x027E3AFF | 02 | 00 |
| 0x027E3B00 | 72 | 00 |
| 0x027E3B05 | 9A | 00 |
| 0x027E3B06 | 0E | 00 |
| 0x027E3B07 | 02 | 00 |
| 0x027E3B08 | 10 | 48 |

Every AQ mapped field remains unchanged: phase/delay/correct-count/result flag 1/1/1/1; +7BC=020E9F70,+7C0=02132750,+7C4=0,+7C8=80000,+7CC=60000,+7F4=1; +7D0/+7D4=1000. No semantic name is assigned to pointee+2C. Save SHA remains a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb; logical requests=0, Flash commits=0, MMIO accesses=0.

AS guard contract (recommendation only): reconstruct AQ independently, verify all CPU flags/mode/masks, full RAM/DTCM/save hashes, ordinal, code/literals/data. Permit only eleven ordered PC/opcode/full-state transitions and five reads. Deny extra fetch/read/write before the bus. Audit all nine PUSH words in ascending order and the local pointer store, exact source/before/readback, including idempotent stores. Validate SP and complete memory at each observation. Deny MMIO, save requests, extra guest/scheduler dispatch, divergence and budget overrun. Halt before terminal fetch/accounting/dispatch, compare complete images/registers. Forbidden next instruction is 02067564, not just MMIO store 02001980. No runtime guard installed.

Read-only reproduction: `python -B tools/task_ar/check.py`. Export only these reports: `python -B tools/task_ar/analyze.py --export`. Checks cover provenance, fixed operand/address/frame arithmetic, reproducibility and negative opcode/source/address/SP/entry tests. No interpreter, replay, runtime build, checkpoint/save mutation, ROM patch, generated-C edit or scheduler refactor. Unrelated jarvis-inbox-v1.zip preserved.

Evidence: exact-ROM static proof anchored in forced Tier-3 exact-context original ARM interpreter AQ evidence; no compiled parity. Predictions require frozen context and future guards. Requested Astra Medium fresh thread could not be selected in this existing thread. Stopped after AR; AS not started.
