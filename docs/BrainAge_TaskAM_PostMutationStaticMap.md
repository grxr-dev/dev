# Task AM - post-mutation static map

**FULL PASS.** Recommend AN from **0x02067BE0 to before 0x02067C44**, exactly **19 instructions**. The first next meaningful action is a value-changing pointer-valued object store, not a return. No post-AL instruction was dynamically executed; AN was not started.

## Evidence and entry

Authoritative AL `7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70`, AK `dd29b71e182611fb73016aa1a13367e70c9cd290`, AJ `a1d2c76baedc0ae841086eeccaf9aa5daebe8d16`. Reports and all tools in those task directories match their commits (line-ending normalized). All are ancestors of initial HEAD `c5b5c5c545e4974f174dfa299370c917b539fa06`; its unrelated work is preserved. Branch `codex/brainage`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework HEAD `3a57236bb23d25dcb4caad7d58d733311062ff5e`.

AL entry r0-r12 (hex): `020E9F70,0,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B04`, LR=`02026010`, PC=`02067BE0`, NZCV=`0/0/1/0`, T=0, mode=31, I=F=0. Ordinal=281097925. The committed stop matches the retained AL audit's last observation and its terminal non-dispatch record. Complete retained RAM/DTCM/save hashes and every mapped field match AL; DTCM hash also matches AK. All relevant ROM words match retained AL RAM. No contradiction with AL/AK/AJ was found.

Main RAM SHA-256 `9f31cfc87f6d2913f83bd98854c4837330dfdef539888c935f6b83aea0688dc9`; DTCM `1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716`; save `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`. Exercise base=020E9A00; subobject r4=exercise+570. +7C4 is already zero.

## Exact prefix and first mutation

All numbers below are hexadecimal unless stated otherwise. All instructions without a named predicate are unconditional AL. Unlisted registers, SP and LR remain unchanged. Only CMP/ANDS change flags. Sequential successors are PC+4; all branch outcomes and targets are explicit. The only data accesses are three aligned ordinary main-RAM object reads; there are no stack, global, unknown or peripheral accesses. No calls, returns or stores intervene.

| PC / opcode | Decode | Exact effect / predicate |
|---|---|---|
| 0x02067BE0 / 0xE3510000 | cmp r1, #0 | CMP 0,0 -> NZCV=0110 |
| 0x02067BE4 / 0xE3A00000 | mov r0, #0 | r0=0; flags unchanged |
| 0x02067BE8 / 0x0A000004 | beq #0x2067c00 | EQ true Z=1 -> 02067C00; skips alternate r1 cases |
| 0x02067C00 / 0xE3520000 | cmp r2, #0 | CMP 0,0 -> NZCV=0110 |
| 0x02067C04 / 0xBA00000D | blt #0x2067c40 | LT false N=V=0; target 02067C40 not taken -> 02067C08 |
| 0x02067C08 / 0xE3520008 | cmp r2, #8 | CMP 0,8 -> NZCV=1000 |
| 0x02067C0C / 0xAA00000B | bge #0x2067c40 | GE false N=1 V=0; target 02067C40 not taken -> 02067C10 |
| 0x02067C10 / 0xE3A00001 | mov r0, #1 | r0=1 |
| 0x02067C14 / 0xE1A00210 | lsl r0, r0, r2 | r0=1 << r2(0) = 1; no flags |
| 0x02067C18 / 0xE59410C0 | ldr r1, [r4, #0xc0] | object read [020EA030] (+630)=1 -> r1 |
| 0x02067C1C / 0xE0110000 | ands r0, r1, r0 | r0=1 & 1=1; NZ=00; zero-shift carry preserved C=0, V=0 |
| 0x02067C20 / 0x0A000006 | beq #0x2067c40 | EQ false Z=0; target 02067C40 not taken -> 02067C24 |
| 0x02067C24 / 0xE0841102 | add r1, r4, r2, lsl #2 | r1=020E9F70+(0 << 2)=020E9F70 |
| 0x02067C28 / 0xE5910080 | ldr r0, [r1, #0x80] | object read [020E9FF0] (+5F0)=44 hex -> r0 |
| 0x02067C2C / 0xE1530000 | cmp r3, r0 | CMP 1F,44 -> NZCV=1000; signed 31 < 68 |
| 0x02067C30 / 0xB5911060 | ldrlt r1, [r1, #0x60] | LT true; object read [020E9FD0] (+5D0)=02131D24 -> r1 |
| 0x02067C34 / 0xB3A00054 | movlt r0, #0x54 | LT true; r0=54 hex |
| 0x02067C38 / 0xB0201093 | mlalt r0, r3, r0, r1 | LT true; r0=1F*54+02131D24=02132750; no flags |
| 0x02067C3C / 0xBA000000 | blt #0x2067c44 | LT true N=1 V=0 -> 02067C44; skips MOV r0,0 |

At **02067C44 / E5840250 / STR r0,[r4,#250]**, address=**020EA1C0=exercise+7C0**, width=4, source r0=**02132750**. Retained before=**02133A18**, predicted after=**02132750**. Little-endian bytes `18 3A 13 02 -> 50 27 13 02`: exactly two changed bytes, at 020EA1C0 and 020EA1C1. No writeback or flag change. This field's semantic role is unproven; the calculation selects base + 31*84 from retained base=02131D24 and bound=68 decimal. The pointed-to data is never dereferenced in the AN prefix. The store is forbidden in AN.

## Static lookahead: full helper tail and return

The following is supplementary static analysis beyond the first mutation, **not an extension of AN**. It answers whether this is merely cleanup: it is not. All direct stores remain within the exercise object; no unknown address is used. All fields below retain offset-only semantics; no score/history/progression meaning is inferred. Before values come from AL; these destinations do not overlap one another.

| Store PC / opcode | Exercise offset / address | Width / source | Before -> after | Effect |
|---|---|---|---|---|
| 0x02067C44 / 0xE5840250 | 0x7c0 / 0x020EA1C0 | 4 / r0 | 0x02133A18 -> 0x02132750 | value-changing |
| 0x02067C50 / 0xE584424C | 0x7bc / 0x020EA1BC | 4 / r4 | 0x020EA034 -> 0x020E9F70 | value-changing |
| 0x02067D10 / 0xE5840278 | 0x7e8 / 0x020EA1E8 | 4 / r0 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D18 / 0xE5842258 | 0x7c8 / 0x020EA1C8 | 4 / r2 | 0x0002D000 -> 0x00000000 | value-changing |
| 0x02067D1C / 0xE584225C | 0x7cc / 0x020EA1CC | 4 / r2 | 0x00060000 -> 0x00000000 | value-changing |
| 0x02067D24 / 0xE5840260 | 0x7d0 / 0x020EA1D0 | 4 / r0 | 0x00001000 -> 0x00001000 | idempotent |
| 0x02067D28 / 0xE5840264 | 0x7d4 / 0x020EA1D4 | 4 / r0 | 0x00001000 -> 0x00001000 | idempotent |
| 0x02067D30 / 0xE1C028B8 | 0x7f8 / 0x020EA1F8 | 2 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D34 / 0xE584226C | 0x7dc / 0x020EA1DC | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D3C / 0xE5842270 | 0x7e0 / 0x020EA1E0 | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D40 / 0xE1C018BA | 0x7fa / 0x020EA1FA | 2 / r1 | 0x0000FFFF -> 0x0000FFFF | idempotent |
| 0x02067D44 / 0xE584227C | 0x7ec / 0x020EA1EC | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D4C / 0xE5840280 | 0x7f0 / 0x020EA1F0 | 4 / r0 | 0xFFFFFFFF -> 0xFFFFFFFF | idempotent |
| 0x02067D50 / 0xE5842268 | 0x7d8 / 0x020EA1D8 | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D58 / 0xE5840274 | 0x7e4 / 0x020EA1E4 | 4 / r0 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D5C / 0xE5842284 | 0x7f4 / 0x020EA1F4 | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |

After C44: C48 MOV r0,r4 sets 020E9F70; C4C MOV r1,r2 sets zero; C50 stores r4 as listed. **02067C54 / EBFFFD95 / BL 020672B0** has r0-r3=`020E9F70,0,0,1F`, SP=027E3B04, LR before=02026010, LR after=02067C58. This is a completely bounded 11-instruction read-only accessor on this state:

- 020672B0 CMP r1,0: 0-0 -> NZCV=0110; B4 BLT 020672DC fails.
- B8 CMP r1,8: 0-8 -> NZCV=1000; BC BGE 020672DC fails.
- C0 MOV r2,1; C4 LSL r2,r2,r1 leaves 1; C8 LDR r3,[r0,C0] reads 020EA030=1.
- CC ANDS r2,r3,r2 gives 1, NZCV=0000 (C preserved from comparison).
- D0 ADDNE r0,r0,r1,LSL 2 leaves 020E9F70; D4 LDRNE r0,[r0,A0] reads 020EA010=0. NE is true for both; loads do not change flags.
- D8 BXNE LR returns in ARM state to 02067C58; SP unchanged. r0-r3=`0,0,1,1`, NZCV=0000. No stack or memory write and no nested call.

02067C58 branches unconditionally to 02067D10. D10 stores r0=0. D14 sets r2=0. D18/D1C store zero; D20 sets r0=1000; D24/D28 store it. D2C sets r0=r4+200=020EA170. D30 stores halfword zero at r0+88. D34 stores zero. D38 LDR r1,[PC,24] reads literal 02067D64=0000FFFF (verified ROM and RAM); D3C stores zero, D40 stores the low halfword FFFF at r0+8A, D44 stores zero. D48 MVN r0,0 sets FFFFFFFF; D4C stores it; D50 stores zero. D54 reads [r4+278]=[020EA1E8]=0, already written at D10; D58 stores that zero at +274; D5C stores zero at +284. None of these operations changes flags.

**02067D60 / E8BD8010 / POP {r4,pc}** reads retained DTCM [027E3B04]=020E9A00 and [027E3B08]=02026010, exactly the AK nested PUSH values. It restores r4=020E9A00, PC=02026010, SP=027E3B0C. LR remains 02067C58 (POP loads PC, not LR); NZCV=0000. No stack byte changes. Thus the nested helper does return cleanly, but only after the listed object stores. Conditional return state r0-r12=`0,FFFF,0,1,020E9A00,0,DA,020E9A00,020E9A00,0,0,0,0`.

## Caller after that conditional return

This is also outside AN. The outer helper at 02025F78 has not returned:

- 02026010 / EA000004 branches to 02026028, skipping the alternate nested invocation at 02026024.
- 02026028 / E3A00001 sets r0=1; **0202602C / E58707F4** writes [020EA1F4]=exercise+7F4, 4 bytes, **0 -> 1**. This is the first caller mutation after the helper's own stores; offset semantics are unproven.
- 02026030 / E3A00702 sets r0=80000; **02026034 / E58707C8** writes 4 bytes at 020EA1C8 (+7C8), **0 -> 80000**. AL held 2D000 here, but the earlier nested D18 store resets it to zero; using AL's value as the immediate before-value here would be incorrect.
- 02026038 / E3A01806 sets r1=60000; 0202603C / E2870E57 sets r0=020E9F70; **02026040 / E58717CC** writes 4 bytes at 020EA1CC (+7CC), **0 -> 60000**. D1C has reset AL's original 60000 to zero.
- **02026044 / EB01053C / BL 0206753C**: r0-r3=`020E9F70,60000,0,1`, SP=027E3B0C, incoming LR=02067C58, link LR=02026048. Expansion stops here: this later callee is not certified by AM and its effects are unknown in this report. No claim is made about returning to 02026258 or further caller behavior. The earlier first mutation is already fully bounded, so this optional lookahead limit does not make the required AM result partial.

The JSON includes exact ROM-checked opcode/decode facts for every instruction on this supplementary path through this call. No MMIO/save/Flash access occurs in the statically mapped helper or caller prefix before that call. The later call has no such guarantee.

## Task AN recommendation

Start at the authoritative AL pre-dispatch **02067BE0** and stop **before fetch/dispatch of 02067C44**, after exactly the 19 prefix instructions above (including condition-failed branches). No return or call is included. This is the largest contiguous write-free prefix: taking one further instruction crosses the first value-changing object boundary. A single-instruction slice is unnecessary.

Expected terminal r0-r12 (hex): **`02132750,02131D24,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`**; SP=**027E3B04**, LR=**02026010**, PC=**02067C44**, NZCV=**1/0/0/0**, T=0, mode=31, I=F=0. Expected ARM9 ordinal **281097944** (+19); ARM7 remains held at 96026779. No cycle estimate is claimed.

Expected architectural RAM/DTCM writes **zero**, byte diffs **zero**, and hashes exactly the AL hashes above. All AL mapped fields remain unchanged: +10=1, +1C=0, +20=1, +34=DA hex, +38=0, +3C=20 decimal, +40=1, +44=1, +4C=4, +58=11 decimal, +504=1, +50C=255 decimal, +514=4, +51C=255 decimal, +7C4=0. Newly read fields +630=1, +5F0=44 hex, +5D0=02131D24 and destination +7C0=02133A18 also remain unchanged. Save byte-identical, requests=0, Flash commits=0, MMIO=0; no gameplay continuation.

Future AN must reconstruct AL and gate the full CPU/flags/mode, exact ROM/code words, retained full RAM/DTCM/save hashes and ordinal before arming. Require the fixed ordered PC/opcode path and exact per-step effects above. Permit only instruction fetches and the three named 32-bit object reads. Reject every write, unknown/MMIO read, call, return, path divergence, extra instruction, scheduler handoff or save request. Stop before the forbidden store regardless of operand equality. These are recommendations, not implemented or tested runtime guards in AM.

## Reproduction and limitations

Run `python tools/task_am/analyze.py` for read-only verification, or append `--export` to regenerate only the JSON. It uses Capstone and explicit static proof obligations; it does not invoke any guest interpreter, emulator, runtime, checkpoint replay, installation or build. Input files are hashed before/after, including all retained AL session files; no guest image is written. Only ROM-free report/helper files are committed. Unrelated `jarvis-inbox-v1.zip` is preserved.

Evidence: exact-ROM static analysis anchored in retained **forced Tier-3 exact-context original-interpreter AL evidence; no compiled parity**. Predictions depend on that frozen state and future guards. Unknown fields have no invented semantic names. The environment's sandbox setup failed before reads; approved escalated filesystem commands were used. **Stopped after AM; AN not begun.**
