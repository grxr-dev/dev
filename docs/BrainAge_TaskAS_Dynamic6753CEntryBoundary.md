# Task AS ? dynamic 0206753C entry boundary

**FULL PASS.** Reconstructed the exact AQ stop and executed AR?s certified **11 original ARM instructions**, halting at **`02067564 / EBFE692A / BL02001A14` before interpreter fetch/accounting/dispatch**. Actual bus ledger: **10 DTCM word writes, eight value-changing and two idempotent**. Exactly **21 DTCM bytes** change; main RAM/save change **zero bytes**.

AR `7b2cbdb1347d5eb639c60f6573f249dd3bb8e3ad`; AQ `06b1432abaac62be3e4649afe58a70b2d5bb793d`. ROM SHA1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Evidence is forced Tier-3 exact-context original ARM interpreter only; no compiled parity.

## Reconstruction and fail-closed guards

Preflight rechecks the committed AR/AQ artifacts, predecessor provenance, full retained AQ images, and the original ROM/state static certificate including AR?s independent ten-word ledger and seven negative checks. AR?s complete full-state/access certificate is frozen before execution and compiled into fixed guards.

Existing deterministic checkpoint restore and exact frozen real-SDL source gesture reconstruct the entire prefix. All112 earlier decision observations and all46 AQ observations, with earlier bus ledgers, match the retained authoritative run exactly. The original private recognizer produces2?4 and tears down before publication; its host hold preserves live CPU/RAM/counters/video/save/touch. No guest registers or execution state are fabricated.

At AS arming, full RAM/DTCM/save hashes, all16 registers/NZCV/T/mode/masks, instruction ordinal/cycles, all12 code words (11 permitted plus forbidden terminal), all ten DTCM before-words and all five literal/object/pointee read values are revalidated independently. Every observation enforces complete expected CPU and images plus exact completed read/write counts.

The opt-in control precedes bank handoff, accounting, instruction fetch and Interpreter::step. Actual RtBus adapters reject any unexpected/repeated/skipped PC, opcode, address, width, source, immediate-before value, read/write count, MMIO or instruction-budget overrun before underlying bus access. The ten writes are ordered individually, even the nine writes belonging to one PUSH. Readback is checked after each actual write; only a diagnostic expected-DTCM buffer is updated. No main-RAM write is permitted in AS.

Pre-execution helper build issues (output header path and private replay namespace collision) were corrected before any guest replay. Auditor predecessor ledger labels were corrected without further guest execution. No divergence from AR or alteration of predecessor source/evidence.

## Exact original instruction path

| PC / opcode | Decode | Actual effect |
|---|---|---|
| `0x02026044 / 0xEB01053C` | `bl #0x206753c` | BL creates LR=02026048; target=0206753C |
| `0x0206753C / 0xE92D4FF0` | `push {r4, r5, r6, r7, r8, sb, sl, fp, lr}` | Save r4-r11,LR in ascending DTCM words; SP -= 24 hex |
| `0x02067540 / 0xE59FC5A4` | `ldr ip, [pc, #0x5a4]` | r12=[02067AEC]=48C |
| `0x02067544 / 0xE04DD00C` | `sub sp, sp, ip` | SP -= r12(48C); allocation writes no memory |
| `0x02067548 / 0xE2804F93` | `add r4, r0, #0x24c` | r4=r0+24C=exercise+7BC |
| `0x0206754C / 0xE5949014` | `ldr sb, [r4, #0x14]` | r9=[exercise+7D0]=1000 |
| `0x02067550 / 0xE5941004` | `ldr r1, [r4, #4]` | r1=[exercise+7C0]=02132750 |
| `0x02067554 / 0xE58D000C` | `str r0, [sp, #0xc]` | Save r0 at SP+C=027E3668 (idempotent) |
| `0x02067558 / 0xE1A00009` | `mov r0, sb` | r0=r9=1000 |
| `0x0206755C / 0xE591A02C` | `ldr sl, [r1, #0x2c]` | r10=[02132750+2C]=020FD00C; unnamed pointee field |
| `0x02067560 / 0xE5948018` | `ldr r8, [r4, #0x18]` | r8=[exercise+7D4]=1000 |

All predicates are AL; NZCV remains0000. BL02026044 creates LR02026048 and enters0206753C. PUSH saves r4?r11/LR in ascending words and changes SP027E3B0C?027E3AE8. SUB allocates48C bytes, changing SP?027E365C without initializing locals. STR02067554 saves r0 atSP+C=027E3668. No nested call or return occurs.

## Ten actual DTCM write events

Observed path: Interpreter::step ? RtBus::write32 ? original bus_write_u32. These are architectural bus events independently audited from the final byte diff. All events match AR; all widths are4.

| PC / opcode | Address | Source/value | Immediate before ? after | Class |
|---|---|---|---|---|
| `0206753C / E92D4FF0` | `027E3AE8` | r4=`020E9A00` | `020EA644 ? 020E9A00` | value-changing |
| `0206753C / E92D4FF0` | `027E3AEC` | r5=`00000000` | `00000000 ? 00000000` | idempotent |
| `0206753C / E92D4FF0` | `027E3AF0` | r6=`000000DA` | `020E9A00 ? 000000DA` | value-changing |
| `0206753C / E92D4FF0` | `027E3AF4` | r7=`020E9A00` | `00000000 ? 020E9A00` | value-changing |
| `0206753C / E92D4FF0` | `027E3AF8` | r8=`020E9A00` | `00000001 ? 020E9A00` | value-changing |
| `0206753C / E92D4FF0` | `027E3AFC` | r9=`00000000` | `020E9A00 ? 00000000` | value-changing |
| `0206753C / E92D4FF0` | `027E3B00` | r10=`00000000` | `00000072 ? 00000000` | value-changing |
| `0206753C / E92D4FF0` | `027E3B04` | r11=`00000000` | `020E9A00 ? 00000000` | value-changing |
| `0206753C / E92D4FF0` | `027E3B08` | r14=`02026048` | `02026010 ? 02026048` | value-changing |
| `02067554 / E58D000C` | `027E3668` | r0=`020E9F70` | `020E9F70 ? 020E9F70` | idempotent |

The two idempotent writes are saved r5 at027E3AEC and saved r0 at027E3668. They remain actual counted events. Stack allocation itself writes no memory.

## CPU, data reads and full-image audit

Final r0?r12=`1000,02132750,0,1,020EA1BC,0,DA,020E9A00,1000,1000,020FD00C,0,48C`; SP=`027E365C`, LR=`02026048`, PC=`02067564`, NZCV=`0000`, T/mode/I/F=0/31/0/0. Every intermediate state matches AR.

| Changed register | AQ before | AS after |
|---|---|---|
| r0 | `0x020E9F70` | `0x00001000` |
| r1 | `0x00060000` | `0x02132750` |
| r4 | `0x020E9A00` | `0x020EA1BC` |
| r8 | `0x020E9A00` | `0x00001000` |
| r9 | `0x00000000` | `0x00001000` |
| r10 | `0x00000000` | `0x020FD00C` |
| r12 | `0x00000000` | `0x0000048C` |
| SP | `0x027E3B0C` | `0x027E365C` |
| LR | `0x02067C58` | `0x02026048` |
| PC | `0x02026044` | `0x02067564` |

Unlisted registers/flags remain unchanged.

| Actual data-read PC | Address | Width | Value |
|---|---|---|---|
| `0x02067540` | `0x02067AEC` | 4 | `0x0000048C` |
| `0x0206754C` | `0x020EA1D0` | 4 | `0x00001000` |
| `0x02067550` | `0x020EA1C0` | 4 | `0x02132750` |
| `0x0206755C` | `0x0213277C` | 4 | `0x020FD00C` |
| `0x02067560` | `0x020EA1D4` | 4 | `0x00001000` |

**Full4MiB main RAM is byte-identical**, SHA256 before=after `84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340`. Complete16KiB DTCM comparison has exactly the following21 changed bytes; no others. DTCM before=`1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716`, after=`48b89027a274b3268219cdc6a8cd1f7fe15bf442a78b3931d79c4e6ae3ea36e4`.

| DTCM address | Before | After |
|---|---|---|
| `0x027E3AE8` | `44` | `00` |
| `0x027E3AE9` | `A6` | `9A` |
| `0x027E3AF0` | `00` | `DA` |
| `0x027E3AF1` | `9A` | `00` |
| `0x027E3AF2` | `0E` | `00` |
| `0x027E3AF3` | `02` | `00` |
| `0x027E3AF5` | `00` | `9A` |
| `0x027E3AF6` | `00` | `0E` |
| `0x027E3AF7` | `00` | `02` |
| `0x027E3AF8` | `01` | `00` |
| `0x027E3AF9` | `00` | `9A` |
| `0x027E3AFA` | `00` | `0E` |
| `0x027E3AFB` | `00` | `02` |
| `0x027E3AFD` | `9A` | `00` |
| `0x027E3AFE` | `0E` | `00` |
| `0x027E3AFF` | `02` | `00` |
| `0x027E3B00` | `72` | `00` |
| `0x027E3B05` | `9A` | `00` |
| `0x027E3B06` | `0E` | `00` |
| `0x027E3B07` | `02` | `00` |
| `0x027E3B08` | `10` | `48` |

| Audited exercise field | AQ before | AS after |
|---|---|---|
| 0x10 | `00000001` | `00000001` |
| 0x20 | `00000001` | `00000001` |
| 0x34 | `000000DA` | `000000DA` |
| 0x44 | `00000001` | `00000001` |
| 0x1C | `00000000` | `00000000` |
| 0x3C | `00000014` | `00000014` |
| 0x40 | `00000001` | `00000001` |
| 0x58 | `0000000B` | `0000000B` |
| 0x4C | `00000004` | `00000004` |
| 0x504 | `00000001` | `00000001` |
| 0x51C | `000000FF` | `000000FF` |
| 0x38 | `00000000` | `00000000` |
| 0x50c | `000000FF` | `000000FF` |
| 0x514 | `00000004` | `00000004` |
| 0x7c4 | `00000000` | `00000000` |
| 0x630 | `00000001` | `00000001` |
| 0x5f0 | `00000044` | `00000044` |
| 0x5d0 | `02131D24` | `02131D24` |
| 0x7c0 | `02132750` | `02132750` |
| 0x7bc | `020E9F70` | `020E9F70` |
| 0x7e8 | `00000000` | `00000000` |
| 0x7c8 | `00080000` | `00080000` |
| 0x7cc | `00060000` | `00060000` |
| 0x7d0 | `00001000` | `00001000` |
| 0x7d4 | `00001000` | `00001000` |
| 0x7f8 | `00000000` | `00000000` |
| 0x7dc | `00000000` | `00000000` |
| 0x7e0 | `00000000` | `00000000` |
| 0x7fa | `0000FFFF` | `0000FFFF` |
| 0x7ec | `00000000` | `00000000` |
| 0x7f0 | `FFFFFFFF` | `FFFFFFFF` |
| 0x7d8 | `00000000` | `00000000` |
| 0x7e4 | `00000000` | `00000000` |
| 0x7f4 | `00000001` | `00000001` |
| 0x610 | `00000000` | `00000000` |

All35 audited fields are unchanged. Phase/delay/correct-count/result flag remain1/1/1/1; +7BC=020E9F70,+7C0=02132750,+7C4=0,+7C8=80000,+7CC=60000,+7F4=1. No main-RAM/object/gameplay/progression/history/result-completion/resume effect occurs in AS; only the certified saved-frame/local DTCM stores. Scene/video/touch/owners remain unchanged. No semantic name is assigned to the pointee+2C read.

Save before=after SHA256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; changed bytes0; logical save requests0; Flash commits0; dirtyfalse. Source checkpoint/save remain immutable. MMIO accesses0: the complete bus ledger has11 instruction fetches, five certified main-RAM literal/object/pointee reads and ten DTCM writes.

## Accounting and forbidden nested call

| Counter | Before | After | Delta |
|---|---|---|
| insn9 | 281097990 | 281098001 | 11 |
| cycle9 | 3416875664 | 3416875700 | 36 |
| insn7 | 96026779 | 96026779 | 0 |
| cycle7 | 1708437825 | 1708437825 | 0 |

No accounting was restored or synthesized. Exactly11 ARM9 instructions,36 ARM9 cycles; ARM7 instruction/cycle deltas both0.

**02067564 was not fetched by the interpreter, dispatched or executed.** The16-read ledger excludes its fetch; only debug opcode inspection occurs. No instruction at02001A14,02001974 or020019B0 ran. Terminal ABI for the forbidden call: r0?r3=`1000,02132750,0,1`, SP=`027E365C`, incoming LR=`02026048`; BL would create LR02067568 and target02001A14.

AR?s static lookahead establishes that the excluded path reaches MMIO writes and busy-bit polling. AS establishes no whole-callee termination/device semantics and no return. The meaningful safe boundary is before the nested external operation, after the fully certified prologue/argument setup.

## Validation and reproduction

Seven focused groups pass: AS?s404 positive/negative full-state/path/opcode/budget/read/write assertions; AO?s11 prior guard checks; unchanged publication policy; hook-order/single underlying bus-call verification; exact AQ table reuse; production source identity; frozen-table reproducibility. Build passes with existing Task S indentation warnings only. Disabled control has no input/staging/decision effects and zero RAM/save changes. Authoritative replay and exhaustive audit exit cleanly with no forced cleanup.

```powershell
python tools/task_as/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_as/build.ps1
python tools/task_as/check.py
python tools/task_as/run.py --out local/task-as/disabled-repro --disabled --port 20601
python tools/task_as/run.py --out local/task-as/session-repro --port 20602
python tools/task_as/analyze.py --out local/task-as/session-repro --disabled local/task-as/disabled-repro --export local/task-as/repro-result.json
```

Fresh output directories required. Raw RAM/save/state/window/log evidence is ignored under local/task-as. Only ROM-free helpers, proof constants and Markdown/JSON are committed. No ROM, generated recomp-C/binary, save/checkpoint or assets committed; no scheduler refactor, ROM patch, production source change or arbitrary guest-call API. Unrelated jarvis-inbox-v1.zip remains untouched.

Recommended next smallest task: separately authorized read-only analysis of the pending02067564?02001A14 operation and its required MMIO semantics/safety boundary. Do not dynamically cross it based on this entry-prefix proof. **Stopped after AS; no successor task started.**
