# Task AT - nested MMIO static map

**FULL PASS for the static contract and safe AU recommendation.** From the AS stop, AU should execute exactly **seven original ARM instructions** and halt at **02001980 / E1C130B0 / STRH r3,[r1] before fetch, accounting or dispatch**. This is the largest contiguous deterministic setup prefix before the first MMIO access. AT performed no guest execution and did not start AU.

AS commit: 72c93f2eb0a561ff4b047d171e904477d8553e7b. AR commit: 7b2cbdb1347d5eb639c60f6573f249dd3bb8e3ad. ROM SHA-1: b8a105bacc3234dede8d4465df0869f2b922a0e2. Pinned ndsrecomp HEAD: 3a57236bb23d25dcb4caad7d58d733311062ff5e. All addresses, opcodes and register values below are hexadecimal unless identified as counts.

## AS entry re-established

The static certificate checks committed AS/AR reports and all their tracked helpers against the authoritative commits; retained AS observations and actual read/write ledgers against committed evidence and AR predictions; the terminal non-fetch/non-dispatch event; complete RAM/DTCM/save hashes; all 35 mapped fields; the prior 21-byte AS DTCM diff; and immutable save/request/Flash evidence. It reads files only. The ROM header locates ARM9 code, and each mapped opcode and all five pointer literals are checked against both the exact ROM and retained AS main RAM. The JSON records every input SHA-256, full prefix states, code facts and literal values.

Entry r0-r12:
00001000,02132750,00000000,00000001,020EA1BC,00000000,000000DA,020E9A00,00001000,00001000,020FD00C,00000000,0000048C.
SP=027E365C, LR=02026048, PC=02067564, NZCV=0000; T/mode/I/F=0/31/0/0; ARM9 ordinal=281098001. AS had 11 instructions, 16 reads including fetches, ten DTCM word writes, zero MMIO, zero logical save requests and zero Flash commits. The pending BL was not fetched or dispatched.

| Full image | AS terminal SHA-256 |
|---|---|
| Main RAM, 4 MiB | 84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340 |
| DTCM, 16 KiB | 48b89027a274b3268219cdc6a8cd1f7fe15bf442a78b3931d79c4e6ae3ea36e4 |
| Save | a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb |

## Pending-call ABI, safe setup and frame

02067564 contains EBFE692A. ARM BL target = PC+8+sign_extend(imm24<<2) = 02001A14; LR created=02067568. Exact incoming r0-r3=1000,02132750,0,1; incoming SP/LR=027E365C/02026048. On the mapped wrapper path, r0 is the denominator input; incoming r1-r3 are not consumed before being overwritten. No object is dereferenced.

| PC / opcode | Instruction | Exact effect before first MMIO |
|---|---|---|
| 02067564 / EBFE692A | BL 02001A14 | LR=02067568; target wrapper |
| 02001A14 / E92D4000 | STMDB SP!,{LR} | SP=027E3658; write word 02067568 to DTCM 027E3658 |
| 02001A18 / E24DD004 | SUB SP,SP,#4 | SP=027E3654; no memory initialization |
| 02001A1C / EBFFFFD4 | BL 02001974 | LR=02001A20; target setup leaf |
| 02001974 / E59F1028 | LDR r1,[PC,#28] | Read main-RAM literal 020019A4=04000280 |
| 02001978 / E3A03001 | MOV r3,#1 | r3=1; no flags |
| 0200197C / E59F2024 | LDR r2,[PC,#24] | Read main-RAM literal 020019A8=04000290 |

Every predicate in this prefix is AL; every instruction preserves NZCV. All seven instruction fetches are main RAM containing ROM-loaded ARM9 code, not cartridge ROM bus reads. Data accesses are exactly two main-RAM word literal reads and one DTCM word store. There is no MMIO, save/Flash, other-address-space or object access.

The first value-changing memory operation is the wrapper's saved-LR store at 02001A14. Its entire effect is certified: [027E3658] changes 02067AE0 -> 02067568. The four allocated bytes 027E3654..027E3657 are untouched. The wrapper has an eight-byte frame (four saved LR bytes plus four unused bytes); the leaves allocate no stack. LR changes at each BL. Safe-prefix r0,r4-r12 are preserved; r1/r2 are clobbered; r3 is explicitly assigned its existing value 1. Full-call r4-r11 are preserved; r0-r3,r12,LR and flags are caller-clobbered. No return occurs before the AU stop.

## Full nested path through hardware and conditional return

This table is **static lookahead, excluded from AU**. It reaches every instruction of this wrapper and both nested leaves. No path is taken dynamically by AT.

| PC / opcode | Instruction | Exact effect / address classification |
|---|---|---|
| 02001980 / E1C130B0 | STRH r3,[r1] | MMIO write 2 bytes: [04000280]=0001 |
| 02001984 / E3A0C000 | MOV r12,#0 | r12=0 |
| 02001988 / E582C000 | STR r12,[r2] | MMIO write 4 bytes: [04000290]=00000000 |
| 0200198C / E3A03A01 | MOV r3,#1000 | ARM rotated immediate gives r3=1000 |
| 02001990 / E59F1014 | LDR r1,[PC,#14] | Main-RAM word literal [020019AC]=04000298 |
| 02001994 / E5823004 | STR r3,[r2,#4] | MMIO write 4 bytes: [04000294]=00001000 |
| 02001998 / E5810000 | STR r0,[r1] | MMIO write 4 bytes: [04000298]=00001000 |
| 0200199C / E581C004 | STR r12,[r1,#4] | MMIO write 4 bytes: [0400029C]=00000000 |
| 020019A0 / E12FFF1E | BX LR | AL; LR=02001A20, bit0=0: return ARM, SP unchanged |
| 02001A20 / EBFFFFE2 | BL 020019B0 | AL; LR=02001A24; enters wait/result leaf |
| 020019B0 / E59F102C | LDR r1,[PC,#2C] | Main-RAM word literal [020019E4]=04000280 |
| 020019B4 / E1D100B0 | LDRH r0,[r1] | MMIO read 2 bytes [04000280], zero-extended status |
| 020019B8 / E2100902 | ANDS r0,r0,#8000 | Mask sampled status bit15; N=0, Z=(masked==0), C=0, V preserved=0 |
| 020019BC / 1AFFFFFC | BNE 020019B4 | Only conditional branch: Z=0/busy set -> repeat; Z=1/busy clear -> 020019C0 |
| 020019C0 / E59F1020 | LDR r1,[PC,#20] | Main-RAM word literal [020019E8]=040002A0 |
| 020019C4 / E3A00702 | MOV r0,#80000 | Rounding bias; no flag update |
| 020019C8 / E5912000 | LDR r2,[r1] | MMIO read 4 bytes [040002A0], quotient low Qlo |
| 020019CC / E5911004 | LDR r1,[r1,#4] | MMIO read 4 bytes [040002A4], quotient high Qhi; address uses old r1 |
| 020019D0 / E0920000 | ADDS r0,r2,r0 | r0=(Qlo+80000) mod 2^32; NZCV from this 32-bit addition |
| 020019D4 / E2A11000 | ADC r1,r1,#0 | r1=(Qhi+carry) mod 2^32; preserves flags |
| 020019D8 / E1A00A20 | MOV r0,r0,LSR #20 decimal | Shift right by decimal 20 (hex 14); preserves flags |
| 020019DC / E1800601 | ORR r0,r0,r1,LSL #12 decimal | Shift left by decimal 12 (hex C); preserves flags |
| 020019E0 / E12FFF1E | BX LR | AL; LR=02001A24, bit0=0: ARM return, SP unchanged |
| 02001A24 / E28DD004 | ADD SP,SP,#4 | SP=027E3658; no memory access |
| 02001A28 / E8BD8000 | LDMIA SP!,{PC} | DTCM word read [027E3658]=02067568; SP=027E365C; return to caller |

The remaining literal words are data, not dispatched instructions. All fetches in this table are main RAM. All predicates other than the identified NE are AL. Apart from the listed MMIO and literal reads, only the final saved-LR DTCM read occurs. There are no further DTCM stores and no main-RAM/object/save/Flash stores. No instruction from the caller's continuation at 02067568 is included.

Helper 02001974 receives r0-r3=1000,02132750,0,1, SP=027E3654, incoming LR=02067568; BL02001A1C creates LR=02001A20. Its twelve instructions are straight-line and architecturally bounded, provided individual bus operations return. It leaves r0-r3=1000,04000298,04000290,1000; r12=0, SP unchanged, NZCV=0000, r4-r11 unchanged. Its five MMIO writes make it unsuitable for AU.

Helper 020019B0 receives r0-r3=1000,04000298,04000290,1000; r12=0, SP=027E3654, incoming LR=02001A20; BL02001A20 creates LR=02001A24. It has 10+3k instructions for k>=1 status samples, with **no program-local upper bound on k**. It leaves r3/r4-r12/SP/LR unchanged from its entry (r12 is already zero). It clobbers r0/r1/r2/NZCV. The wrapper has a bounded frame and straight-line skeleton but is not unconditionally bounded because it calls this polling helper.

## Concrete MMIO contract

Register identities below are established by the repository's runner/src/io.cpp math-register address map and division implementation. No ROM/SDK symbol name for the helpers is asserted. The code has the arithmetic behavior of a rounded fixed-point reciprocal, but no SDK function-name attribution is needed.

| Instruction | Address / width | Direction and value | Source / meaning |
|---|---|---|---|
| 02001980 / E1C130B0 | 04000280 / 2 | Write 0001 | r3 explicitly set to 1; DIVCNT mode bits=1 |
| 02001988 / E582C000 | 04000290 / 4 | Write 00000000 | r12=0; numerator low |
| 02001994 / E5823004 | 04000294 / 4 | Write 00001000 | r3=1000; numerator high |
| 02001998 / E5810000 | 04000298 / 4 | Write 00001000 | original AS r0; denominator low |
| 0200199C / E581C004 | 0400029C / 4 | Write 00000000 | r12=0; denominator high |
| 020019B4 / E1D100B0 | 04000280 / 2 | Read repeatedly; test 8000 | busy=1 loops; busy=0 exits; ignores other status bits |
| 020019C8 / E5912000 | 040002A0 / 4 | Read Qlo after busy clears | quotient low; conditional expected 00000000 |
| 020019CC / E5911004 | 040002A4 / 4 | Read Qhi after busy clears | quotient high; conditional expected 00000001 |

Pointers derive from the five ROM-verified literal words above. Every address is aligned for its access width. MMIO before-values are deliberately not invented or read. The final operand set is signed 64-bit numerator 0000100000000000 (2^44), signed 32-bit denominator 00001000 (2^12), mode 1. The final quotient is 0000000100000000 (2^32), remainder zero. The wait leaf returns low32((Q+80000)>>20 decimal), hence r0=1000 under these operand/completion assumptions.

### Current interpreter bus and exact modeled side effects

The certificate hashes current local sources and verifies the relevant ten io.cpp function bodies are identical to the pinned baseline. Other historical local runtime/diagnostic changes exist and are preserved. Current source anchors:

- runner/src/tier3.cpp:149-154: RtBus adapters forward 16/32-bit accesses to bus_read/write_u16/u32 after diagnostic guards. Existing AS guards stop earlier; this describes the underlying model, not an action allowed by AS.
- runner/src/bus.cpp:419-434,903-968: 04000000..04FFFFFF routes through the I/O funnel with the original width.
- runner/src/io.cpp:3238,3284,3395,3455: ARM9 (cpu==0) reads/writes in math_addr route to math_reg_read32/math_reg_write. Read masking preserves the halfword width. The math handlers return directly without FIFO, DMA, Flash or IRQ handling.
- runner/src/io.cpp:491-532: exact address map and width-aware merge. The first halfword write replaces all 16 DIVCNT bits with 0001, then start_div sets bit15, yielding 8001. Numerator/denominator/result arrays are unchanged by that first write. **Every one of the five writes calls start_div**, even an idempotent operand write, and replaces the completion deadline. Result/remainder registers retain their prior values until completion.
- runner/src/io.cpp:377-410: active_system_timestamp is ARM9 g_runtime_cycles>>1; start_div schedules current system time+34 for mode 1 (68 ARM9-cycle equivalent, not an instruction or polling-count prediction).
- runner/src/runtime_arm.cpp:1186: nds_reschedule_slice converts the system deadline to active-CPU cycles, sets g_cycle_cap and invalidates g_nds_fast_limit only when the cap is zero or the new deadline is earlier than the existing cap. Thus the first write already changes peripheral and scheduling state.
- runner/src/io.cpp:413-465,2233,2283-2335: nds_next_system_event_time includes the divider deadline; nds_run_system_events completes a due division, resets deadline to UINT64_MAX, clears busy/divide-by-zero bits, computes quotient/remainder, and sets divide-by-zero only if both denominator words are zero.
- runner/src/scheduler.cpp:518,525: event service is called at scheduler rendezvous. MMIO status/result reads themselves simply return current values; they do not advance time or invoke finish_div.

The model's division completion has **no inherent DMA, IRQ, FIFO, save/Flash or ARM7 cooperation requirement**. It requires time advancement and servicing the scheduled event. The normal scheduler may run other work while reaching that event; AT does not certify or permit that work. A manually stepped interpreter that never services system events can poll forever even as instruction accounting advances. The exact failing condition is repeated 020019B4 reads with bit15=1 followed by Z=0 at 020019B8 and the taken 020019BC BNE.

The first write can restart division using inherited operands; intermediate writes can also complete using partially updated operands if enough time passes. Exact inherited peripheral state, intermediate results, deadlines and poll count are not reconstructed from AS's CPU/RAM evidence. After the final store, with no interference and correct event service, mode remains 1, final DIVCNT becomes 0001 and quotient/remainder have the values above. This is a static implication of the source, not an observed MMIO result or a hardware-timing parity claim. These are sufficient reasons to stop **before the first write**, even though a model exists.

### Conditional returns, not unconditional completion

If all five stores return, no other writer changes divider operands, the final timed operation completes, quotient reads are coherent, and the saved LR remains intact: setup BX returns 02001A20; wait BX returns 02001A24; wrapper POP returns 02067568. The wrapper restores SP=027E365C. At that caller continuation r0-r12 would be:

00001000,00000001,00000000,00001000,020EA1BC,00000000,000000DA,020E9A00,00001000,00001000,020FD00C,00000000,00000000.

LR remains 02001A24 (POP restores PC, not LR); NZCV=0000 from ADDS 00000000+00080000. The saved-LR DTCM word remains 02067568 after return; it is not erased. All 35 mapped exercise fields remain unchanged by these instructions, but arbitrary scheduler/interleaving effects are outside this conditional statement. There are five MMIO writes, k+2 MMIO reads, and one DTCM word write. Neither this return nor any hardware access is included in AU.

## Exact Task AU recommendation

Execute this sequence only:
02067564 -> 02001A14 -> 02001A18 -> 02001A1C -> 02001974 -> 02001978 -> 0200197C.
Stop at **02001980**, before any fetch/accounting/dispatch of its MMIO store. Count: seven instructions, seven instruction fetches, two data-read words, one DTCM word write. Predicted ARM9 ordinal=281098008. No cycle count or scheduler progression is certified.

Final r0-r12:
00001000,04000280,04000290,00000001,020EA1BC,00000000,000000DA,020E9A00,00001000,00001000,020FD00C,00000000,0000048C.
SP=027E3654, LR=02001A20, PC=02001980, NZCV=0000, T/mode/I/F=0/31/0/0.

| Expected DTCM word event | Before | After |
|---|---|---|
| 02001A14 / E92D4000, LR -> [027E3658], width 4 | 02067AE0 | 02067568 |

| Exact changed byte | Before | After |
|---|---|---|
| 027E3658 | E0 | 68 |
| 027E3659 | 7A | 75 |

Bytes 027E365A/B remain 06/02. No other DTCM byte changes. JSON includes the predicted complete DTCM hash. Main RAM/save remain byte-identical to AS. All 35 mapped fields remain unchanged, including phase/delay/count/result=1/1/1/1; +7BC=020E9F70,+7C0=02132750,+7C4=0,+7C8=00080000,+7CC=00060000,+7D0/+7D4=1000,+7F4=1. Expected logical save requests=0, Flash commits=0, MMIO accesses=0. No progression/history/result-completion behavior is reached.

**Forbidden next effect:** 02001980/E1C130B0 writes halfword 0001 to 04000280, starts/restarts the divider, sets busy and changes scheduling. Reject it before the underlying bus handler. Do not extend to polling or return.

### Required fail-closed AU guards (recommendation; not implemented)

1. Independently reconstruct AS using its existing authorized provenance; do not fabricate CPU state. Verify authoritative commits, exact ROM/baseline, frozen whole RAM/DTCM/save hashes, all registers/NZCV/T/mode/I/F, ARM9 ordinal, all mapped code/literals, saved-word before-value, and no outstanding diagnostic failure before arming.
2. Freeze the seven full pre/post states and exact ordered read/write ledger from this certificate. Compare every expected PC/opcode and complete CPU state before accounting/fetch/dispatch. Reject skipped/repeated/unexpected PCs, wrong mode/flags, opcodes, literals, or budget >7.
3. Allow only seven main-RAM code fetches, the two listed 4-byte literal reads, and the single ordered 4-byte DTCM store. Check store address, source LR, width, immediate-before 02067AE0 and readback 02067568. Reject extra/repeated accesses before the bus. Deny all MMIO, unexpected RAM/DTCM writes, other address spaces, save requests and Flash operations.
4. Halt at 02001980 before fetch/accounting/dispatch and before bank handoff. A debug opcode comparison must be a direct frozen-image inspection, not a runtime bus read. Keep the terminal instruction outside the fetch ledger.
5. Audit full images, registers/flags, exact two-byte diff, unchanged fields/save, seven ARM9 instruction delta and zero MMIO at halt. Reject any extra guest/ARM7 dispatch or unaccounted scheduler/peripheral activity during the prefix. Do not infer a cycle limit from the instruction count; if the environment cannot preserve this scope, stop without crossing the boundary.
6. Preserve live state on failure; do not retry past a mismatch, patch code, bypass existing AS guards, repair state, or roll counters back. Any future AU must install separately reviewed successor guards; AT does not change AS authorization.

## Static validation and limits

Run python -B tools/task_at/check.py. Export only the JSON report with python -B tools/task_at/analyze.py --export. The helper reads files and uses git solely for provenance reads; it has no interpreter, runtime bus, replay, scheduler or checkpoint mutation API. Tests cover exact-ROM/state certificates, opcode/entry/SP/source/literal/MMIO contract rejection, independent frame arithmetic and the known final division arithmetic. They never run the device implementation. Input hashes before/after enforce read-only evidence preservation.

Clean-retry verification: the pre-existing uncommitted AT draft was reviewed against the ROM certificate and current bus/divider/scheduler source. The static checker was rerun successfully, including all 11 negative checks; no predecessor replay or runtime was launched. The divider reschedule description was clarified to reflect its conditional cycle-cap update.

The report is exact-ROM static proof anchored in forced Tier-3 AS original-ARM interpreter evidence. No compiled parity, new dynamic observation, cycle/poll bound, or whole enclosing 0206753C completion claim. The requested Astra Medium fresh thread could not be selected in this existing thread; no claim that the requested model setting was used. The shell sandbox setup failed before command execution, so approved file-only commands were used outside that failing setup. No runtime sources, generated recomp-C, ROM, checkpoint or save were changed. The unrelated jarvis-inbox-v1.zip is preserved.

**Stopped after Task AT. AU is a recommendation only.**
