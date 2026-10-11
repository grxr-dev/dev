# Task AP - post-AO static map

**FULL PASS.** Recommend one AQ experiment from `0x02067C48` through **45 instructions**, stopping **before fetch/dispatch of `0x02026044 / EB01053C / BL 0x0206753C`**. AP performed static reads only; AQ was not started.

AO/AN/AM commits: `3e2ecf215823ad1e5b95a4af830d4ee6026152e0`, `0f3d697861a8d52f569ec051915258e02915d878`, `cb2126cfa0c2e75714b993cdc0124c49c8e1b680`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. All required reports/helpers match these commits (line-ending normalized). AO retained CPU/audit, terminal non-dispatch record, full RAM/DTCM/save and every mapped field were revalidated. Every mapped instruction and literal matches verified ROM and retained RAM.

Entry r0-r12: `02132750,02131D24,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B04`, LR=`02026010`, PC=`02067C48`, NZCV=`1000`, T=0, mode=31, I=F=0, ARM9 ordinal=281097945.

Entry SHA-256: {"mainram": "541991ee1d577324f15893effad69140c1aa0e2d7aeb3a8d302eabbae01e24bd", "dtcm": "1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716", "save": "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"}.

**Evidence correction:** AO flags_before/flags_after summary arrays are stale 0010; ao_start/ao_stop named NZCV and retained audit are 1000. AP uses named fields, consistent with AN and STR preserving flags; predecessor artifacts unchanged.

The next meaningful action is `02067C50`: exercise+7BC changes `020EA034 -> 020E9F70`. The larger prefix is safe to propose because every source/address is deterministic, the accessor is bounded, and the nested helper returns cleanly. Continue across the return and three understood caller stores. The next call is a separate substantial operation; stop before it. Reaching it after fully bounding these effects does not trigger the PARTIAL criterion (an unknown call before the next bounded effect).

All numbers below are hexadecimal except counts. Each instruction fetch is ordinary main-RAM code. Unlisted registers, SP/LR and flags remain unchanged. Sequential successor is PC+4 unless stated. The JSON records complete before/after registers, NZCV, predicate and exact successor for every instruction.

| PC / opcode | Decode | Predicate / effect | Data access class |
|---|---|---|---|
| 0x02067C48 / 0xE1A00004 | mov r0, r4 | AL; r0=r4=020E9F70 | instruction fetch only (main RAM code) |
| 0x02067C4C / 0xE1A01002 | mov r1, r2 | AL; r1=r2=0 | instruction fetch only (main RAM code) |
| 0x02067C50 / 0xE584424C | str r4, [r4, #0x24c] | AL; store r4=020E9F70 at exercise+7BC | main RAM object store |
| 0x02067C54 / 0xEBFFFD95 | bl #0x20672b0 | AL; call 020672B0; LR=02067C58; SP unchanged | instruction fetch only (main RAM code) |
| 0x020672B0 / 0xE3510000 | cmp r1, #0 | AL; CMP 0,0: NZCV=0110 | instruction fetch only (main RAM code) |
| 0x020672B4 / 0xBA000008 | blt #0x20672dc | LT false; LT false (N=V=0); fall through; target 020672DC excluded | instruction fetch only (main RAM code) |
| 0x020672B8 / 0xE3510008 | cmp r1, #8 | AL; CMP 0,8: NZCV=1000 | instruction fetch only (main RAM code) |
| 0x020672BC / 0xAA000006 | bge #0x20672dc | GE false; GE false (N=1,V=0); fall through; target 020672DC excluded | instruction fetch only (main RAM code) |
| 0x020672C0 / 0xE3A02001 | mov r2, #1 | AL; r2=1 | instruction fetch only (main RAM code) |
| 0x020672C4 / 0xE1A02112 | lsl r2, r2, r1 | AL; r2=1 << r1(0)=1; flags unchanged | instruction fetch only (main RAM code) |
| 0x020672C8 / 0xE59030C0 | ldr r3, [r0, #0xc0] | AL; r3=[020EA030]=1 (exercise+630) | main RAM object +630 |
| 0x020672CC / 0xE0132002 | ands r2, r3, r2 | AL; r2=1 & 1=1; NZCV=0000; unshifted carry preserved | instruction fetch only (main RAM code) |
| 0x020672D0 / 0x10800101 | addne r0, r0, r1, lsl #2 | NE true; NE true (Z=0); r0=020E9F70+(0<<2)=020E9F70 | instruction fetch only (main RAM code) |
| 0x020672D4 / 0x159000A0 | ldrne r0, [r0, #0xa0] | NE true; NE true; r0=[020EA010]=0 (exercise+610) | main RAM object +610; newly mapped offset |
| 0x020672D8 / 0x112FFF1E | bxne lr | NE true; NE true; BX LR -> 02067C58, T=0; SP unchanged | instruction fetch only (main RAM code) |
| 0x02067C58 / 0xEA00002C | b #0x2067d10 | AL; branch AL -> 02067D10; skip alternate cases | instruction fetch only (main RAM code) |
| 0x02067D10 / 0xE5840278 | str r0, [r4, #0x278] | AL; store r0=0 at exercise+7E8 | main RAM object store |
| 0x02067D14 / 0xE3A02000 | mov r2, #0 | AL; r2=0 | instruction fetch only (main RAM code) |
| 0x02067D18 / 0xE5842258 | str r2, [r4, #0x258] | AL; store r2=0 at exercise+7C8 | main RAM object store |
| 0x02067D1C / 0xE584225C | str r2, [r4, #0x25c] | AL; store r2=0 at exercise+7CC | main RAM object store |
| 0x02067D20 / 0xE3A00A01 | mov r0, #0x1000 | AL; r0=1000 | instruction fetch only (main RAM code) |
| 0x02067D24 / 0xE5840260 | str r0, [r4, #0x260] | AL; store r0=1000 at exercise+7D0 | main RAM object store |
| 0x02067D28 / 0xE5840264 | str r0, [r4, #0x264] | AL; store r0=1000 at exercise+7D4 | main RAM object store |
| 0x02067D2C / 0xE2840C02 | add r0, r4, #0x200 | AL; r0=r4+200=020EA170 | instruction fetch only (main RAM code) |
| 0x02067D30 / 0xE1C028B8 | strh r2, [r0, #0x88] | AL; store low halfword r2=0 at exercise+7F8 | main RAM object store |
| 0x02067D34 / 0xE584226C | str r2, [r4, #0x26c] | AL; store r2=0 at exercise+7DC | main RAM object store |
| 0x02067D38 / 0xE59F1024 | ldr r1, [pc, #0x24] | AL; r1=[PC+8+24]=[02067D64]=FFFF | ROM literal in main RAM |
| 0x02067D3C / 0xE5842270 | str r2, [r4, #0x270] | AL; store r2=0 at exercise+7E0 | main RAM object store |
| 0x02067D40 / 0xE1C018BA | strh r1, [r0, #0x8a] | AL; store low halfword r1=FFFF at exercise+7FA | main RAM object store |
| 0x02067D44 / 0xE584227C | str r2, [r4, #0x27c] | AL; store r2=0 at exercise+7EC | main RAM object store |
| 0x02067D48 / 0xE3E00000 | mvn r0, #0 | AL; r0=FFFFFFFF | instruction fetch only (main RAM code) |
| 0x02067D4C / 0xE5840280 | str r0, [r4, #0x280] | AL; store r0=FFFFFFFF at exercise+7F0 | main RAM object store |
| 0x02067D50 / 0xE5842268 | str r2, [r4, #0x268] | AL; store r2=0 at exercise+7D8 | main RAM object store |
| 0x02067D54 / 0xE5940278 | ldr r0, [r4, #0x278] | AL; r0=[020EA1E8]=0, same word stored at D10 | main RAM object +7E8; D10 dependency |
| 0x02067D58 / 0xE5840274 | str r0, [r4, #0x274] | AL; store r0=0 at exercise+7E4 | main RAM object store |
| 0x02067D5C / 0xE5842284 | str r2, [r4, #0x284] | AL; store r2=0 at exercise+7F4 | main RAM object store |
| 0x02067D60 / 0xE8BD8010 | pop {r4, pc} | AL; POP: r4=[027E3B04]=020E9A00; PC=[027E3B08]=02026010; SP=027E3B0C; LR stays 02067C58 | DTCM stack |
| 0x02026010 / 0xEA000004 | b #0x2026028 | AL; branch AL -> 02026028; skip alternate nested call | instruction fetch only (main RAM code) |
| 0x02026028 / 0xE3A00001 | mov r0, #1 | AL; r0=1 | instruction fetch only (main RAM code) |
| 0x0202602C / 0xE58707F4 | str r0, [r7, #0x7f4] | AL; store r0=1 at exercise+7F4 | main RAM object store |
| 0x02026030 / 0xE3A00702 | mov r0, #0x80000 | AL; r0=80000 | instruction fetch only (main RAM code) |
| 0x02026034 / 0xE58707C8 | str r0, [r7, #0x7c8] | AL; store r0=80000 at exercise+7C8; immediate before is zero | main RAM object store |
| 0x02026038 / 0xE3A01806 | mov r1, #0x60000 | AL; r1=60000 | instruction fetch only (main RAM code) |
| 0x0202603C / 0xE2870E57 | add r0, r7, #0x570 | AL; r0=r7+570=020E9F70 | instruction fetch only (main RAM code) |
| 0x02026040 / 0xE58717CC | str r1, [r7, #0x7cc] | AL; store r1=60000 at exercise+7CC; immediate before is zero | main RAM object store |

All 18 direct stores are already mapped AO fields. Six store events change values; twelve are idempotent. No stack/global/unknown/MMIO store occurs. Store order matters: +7C8 and +7CC are zeroed before the caller sets them; +7CC ends equal to AO despite two value-changing events. Offset names carry no semantic claim.

| PC / opcode | Address / exercise offset | Width / source | Immediate before -> after | Class |
|---|---|---|---|---|
| 0x02067C50 / 0xE584424C | 0x020EA1BC / 0x7bc | 4 / r4 | 0x020EA034 -> 0x020E9F70 | value-changing |
| 0x02067D10 / 0xE5840278 | 0x020EA1E8 / 0x7e8 | 4 / r0 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D18 / 0xE5842258 | 0x020EA1C8 / 0x7c8 | 4 / r2 | 0x0002D000 -> 0x00000000 | value-changing |
| 0x02067D1C / 0xE584225C | 0x020EA1CC / 0x7cc | 4 / r2 | 0x00060000 -> 0x00000000 | value-changing |
| 0x02067D24 / 0xE5840260 | 0x020EA1D0 / 0x7d0 | 4 / r0 | 0x00001000 -> 0x00001000 | idempotent |
| 0x02067D28 / 0xE5840264 | 0x020EA1D4 / 0x7d4 | 4 / r0 | 0x00001000 -> 0x00001000 | idempotent |
| 0x02067D30 / 0xE1C028B8 | 0x020EA1F8 / 0x7f8 | 2 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D34 / 0xE584226C | 0x020EA1DC / 0x7dc | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D3C / 0xE5842270 | 0x020EA1E0 / 0x7e0 | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D40 / 0xE1C018BA | 0x020EA1FA / 0x7fa | 2 / r1 | 0x0000FFFF -> 0x0000FFFF | idempotent |
| 0x02067D44 / 0xE584227C | 0x020EA1EC / 0x7ec | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D4C / 0xE5840280 | 0x020EA1F0 / 0x7f0 | 4 / r0 | 0xFFFFFFFF -> 0xFFFFFFFF | idempotent |
| 0x02067D50 / 0xE5842268 | 0x020EA1D8 / 0x7d8 | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D58 / 0xE5840274 | 0x020EA1E4 / 0x7e4 | 4 / r0 | 0x00000000 -> 0x00000000 | idempotent |
| 0x02067D5C / 0xE5842284 | 0x020EA1F4 / 0x7f4 | 4 / r2 | 0x00000000 -> 0x00000000 | idempotent |
| 0x0202602C / 0xE58707F4 | 0x020EA1F4 / 0x7f4 | 4 / r0 | 0x00000000 -> 0x00000001 | value-changing |
| 0x02026034 / 0xE58707C8 | 0x020EA1C8 / 0x7c8 | 4 / r0 | 0x00000000 -> 0x00080000 | value-changing |
| 0x02026040 / 0xE58717CC | 0x020EA1CC / 0x7cc | 4 / r1 | 0x00000000 -> 0x00060000 | value-changing |

`02067C54 -> 020672B0` is the only included call: r0-r3=`020E9F70,0,0,1F`, SP=`027E3B04`, LR=`02026010 -> 02067C58`. Its 11-instruction path has two object reads (+630=1, newly mapped +610=0), no stores, no nested calls and no stack adjustment. LT/GE fail; NE instructions execute. BXNE at `020672D8` returns to `02067C58`, r0-r3=`0,0,1,1`, NZCV=0000.

The second return, POP at `02067D60`, reads DTCM `027E3B04=020E9A00` and `027E3B08=02026010`; SP becomes `027E3B0C`, r4 becomes exercise base, LR stays `02067C58`. This returns the nested helper only. The outer helper has not returned. No DTCM byte changes.

Forbidden call `02026044 -> 0206753C`: r0-r3=`020E9F70,60000,0,1`, SP=`027E3B0C`, incoming LR=`02067C58`; dispatch would set LR=`02026048`. It is not certified read-only/bounded. Static inspection shows a nine-register PUSH, literal `02067AEC=48C` stack allocation, pointer dereference and a nested BL at `02067564 -> 02001A14`; that helper itself calls `02001974` and `020019B0`. The PUSH would start writing DTCM at `027E3AE8` (SP-24 hex), and later SP would become `027E365C`. No callee execution, whole-callee effect claim, or continuation past this call is authorized by the proposed AQ.

AQ terminal r0-r12: `020E9F70,60000,0,1,020E9A00,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B0C`, LR=`02067C58`, PC=`02026044`, NZCV=`0000`, T=0, mode=31, I=F=0. ARM9 ordinal predicted `281097990` (+45). No cycle or scheduler prediction.

Expected architectural writes: 18 ordinary object writes (16 words, 2 halfwords); final main-RAM diff exactly five bytes:

| Address | AO byte | AQ predicted byte |
|---|---|---|
| 0x020EA1BC | 34 | 70 |
| 0x020EA1BD | A0 | 9F |
| 0x020EA1C9 | D0 | 00 |
| 0x020EA1CA | 02 | 08 |
| 0x020EA1F4 | 00 | 01 |

Only final mapped fields +7BC (`020EA034 -> 020E9F70`), +7C8 (`2D000 -> 80000`), and +7F4 (`0 -> 1`) change. All other AO fields remain equal at the boundary, including +7C0=`02132750`, +7C4=0 and +7CC=`60000`. JSON enumerates all values. Newly mapped +610 remains zero. DTCM/save byte diffs=0; save requests=0; Flash commits=0; MMIO=0. No general gameplay-completion interpretation is established.

**Future AQ guard contract (recommendation, not an implemented runtime):** reconstruct exact AO evidence; check ROM identity, all CPU flags/mode/masks, full RAM/DTCM/save hashes, ordinal, instruction words, and stack words before arming. Permit only the 45 ordered PC/opcode/full-state transitions in JSON, 45 instruction fetches and six data-read words listed there. The D10-dependent read must see the written zero. Permit exactly the 18 ordered store events with exact PC, address, width, source, immediate-before and readback values, including idempotent stores. Deny unexpected/repeated reads or writes before the bus, MMIO, save requests, path divergence, extra call, scheduler handoff or any instruction beyond the budget. Terminal control must run before fetch/accounting/dispatch of `02026044`; validate full CPU and complete memory diffs there, then halt/unwind. Do not merely gate final bytes: transient zeroing of +7CC must be audited.

Validation: static certificate and focused negative checks (wrong opcode, divergent branch, wrong store address/source, wrong stack restoration) pass; report/JSON regeneration is deterministic. Run `python -B tools/task_ap/check.py` for these checks. Reproduce with `python tools/task_ap/analyze.py`; add `--export` to regenerate only the AP Markdown/JSON. Capstone decodes verified ROM words; explicit static arithmetic/proof annotations derive the certificate. There is no ARM interpreter, guest instruction dispatch, replay, build, checkpoint write, ROM patch or generated-C edit. All required predecessor sources and retained AO files are hashed before/after. Only ROM-free AP artifacts are written. Unrelated `jarvis-inbox-v1.zip` remains untouched.

Evidence: exact-ROM static analysis anchored in **forced Tier-3 exact-context original ARM interpreter** AO observations; **no compiled parity**. Predictions require frozen context and future guards. Stopped after AP; AQ not executed.
