# Task AQ ? dynamic helper-tail boundary

**FULL PASS.** Exact AO replay followed AP?s certified **45 original ARM instructions** and halted at **`0x02026044` before interpreter fetch/dispatch** of `EB01053C / BL 0x0206753C`. The actual ledger contains **18 object stores: six value-changing, twelve idempotent**. Full-image changes are exactly five main-RAM bytes and zero DTCM/save bytes.

Forced Tier-3 exact-context original ARM interpreter evidence only; no compiled-path parity. AP `f36f1ac432a5946f1b451e2d437176447163df3f`; AO `3e2ecf215823ad1e5b95a4af830d4ee6026152e0`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`.

## Entry and guarded execution

Preflight checks the committed AP/AO reports/helpers, verifies retained AO full images, runs AP?s exact-ROM static certificate and negatives, and freezes its full-state instruction/store/read map. UTF-8 BOM normalization was corrected in the source comparison before execution; no predecessor artifact changed. AP?s correction of AO?s stale summary NZCV arrays is retained: named/live entry NZCV is **1000**.

Existing immutable Task G checkpoint and frozen Task Y real-SDL gesture reconstruct the entire prefix. All **112** retained AO pre-dispatch CPU/opcode/ordinal observations match exactly, as do earlier AN read/AK write ledgers and the real AO write. No guest register/state is fabricated. The original private recognizer still returns 2 then4 and tears down before publication; the host hold preserves CPU/RAM/counters/video/save/input. Disabled control has no input, staging or decision dispatches and exits with equal RAM/save.

Before arming AQ, the runtime verifies all16 registers, NZCV/T/mode/masks, ordinal/cycles, complete RAM/DTCM/save hashes and all46 code words (45 permitted plus forbidden terminal). Every subsequent observation checks AP?s complete CPU state and ordinal, exact completed-access counts and full expected RAM/DTCM/save. Expected RAM is advanced only after validated actual bus write/readback.

The fixed hook runs before bank handoff, accounting, decoder fetch and Interpreter::step. Before-bus firewalls permit exactly45 fetches, six data reads and18 ordered writes, including both halfwords; any different PC/opcode/path/address/width/source/before value, extra read/write, MMIO or budget overrun rejects before underlying access. Each underlying bus adapter is invoked once. No broad guest-call API, scheduler refactor, ROM patch or generated recomp-C edit.

## Exact executed path

Each decode/opcode, predicate and full before/after state is recorded in the result JSON. The executed sequence is:

```text
02067C48 ? 02067C4C ? 02067C50 ? 02067C54 ? 020672B0
020672B4 ? 020672B8 ? 020672BC ? 020672C0 ? 020672C4
020672C8 ? 020672CC ? 020672D0 ? 020672D4 ? 020672D8
02067C58 ? 02067D10 ? 02067D14 ? 02067D18 ? 02067D1C
02067D20 ? 02067D24 ? 02067D28 ? 02067D2C ? 02067D30
02067D34 ? 02067D38 ? 02067D3C ? 02067D40 ? 02067D44
02067D48 ? 02067D4C ? 02067D50 ? 02067D54 ? 02067D58
02067D5C ? 02067D60 ? 02026010 ? 02026028 ? 0202602C
02026030 ? 02026034 ? 02026038 ? 0202603C ? 02026040
```

LT at020672B4 and GE at020672BC were false; NE at020672D0/D4/D8 was true. Unconditional branches and both return targets matched AP exactly. No unexpected or repeated/skipped instruction occurred.

## Bounded call and returns

`02067C54 -> 020672B0` is the only included BL. Entry r0?r3=`020E9F70,0,0,1F`, SP=`027E3B04`; BL changes LR=`02026010 ->02067C58`. All11 callee instructions were validated. Its two reads are `020EA030=1` (+630) and `020EA010=0` (+610). It writes nothing, makes no nested call and leaves SP unchanged. BXNE at020672D8 returns to02067C58 with r0?r3=`0,0,1,1`, NZCV=0000.

The later POP at02067D60 reads `027E3B04=020E9A00` into r4 and `027E3B08=02026010` into PC. SP becomes027E3B0C; LR remains02067C58. This returns only the nested helper; the outer helper has not returned. Other reads are the literal at02067D64=FFFF and the D10-dependent object read020EA1E8=0. No DTCM writes.

## Actual architectural stores

Actual RtBus write32/write16 -> original bus_write_u32/u16 events were audited independently from byte diffs. All18 match AP exactly. Helper fields retain offset-only names; their gameplay meaning is unproven.

| PC / opcode | Exercise offset / address | Width / source | Immediate before ? actual after | Class |
|---|---|---|---|---|
| `02067C50 / E584424C` | `0x7bc / 020EA1BC` | 4 / r4 | `020EA034 ? 020E9F70` | value-changing |
| `02067D10 / E5840278` | `0x7e8 / 020EA1E8` | 4 / r0 | `00000000 ? 00000000` | idempotent |
| `02067D18 / E5842258` | `0x7c8 / 020EA1C8` | 4 / r2 | `0002D000 ? 00000000` | value-changing |
| `02067D1C / E584225C` | `0x7cc / 020EA1CC` | 4 / r2 | `00060000 ? 00000000` | value-changing |
| `02067D24 / E5840260` | `0x7d0 / 020EA1D0` | 4 / r0 | `00001000 ? 00001000` | idempotent |
| `02067D28 / E5840264` | `0x7d4 / 020EA1D4` | 4 / r0 | `00001000 ? 00001000` | idempotent |
| `02067D30 / E1C028B8` | `0x7f8 / 020EA1F8` | 2 / r2 | `00000000 ? 00000000` | idempotent |
| `02067D34 / E584226C` | `0x7dc / 020EA1DC` | 4 / r2 | `00000000 ? 00000000` | idempotent |
| `02067D3C / E5842270` | `0x7e0 / 020EA1E0` | 4 / r2 | `00000000 ? 00000000` | idempotent |
| `02067D40 / E1C018BA` | `0x7fa / 020EA1FA` | 2 / r1 | `0000FFFF ? 0000FFFF` | idempotent |
| `02067D44 / E584227C` | `0x7ec / 020EA1EC` | 4 / r2 | `00000000 ? 00000000` | idempotent |
| `02067D4C / E5840280` | `0x7f0 / 020EA1F0` | 4 / r0 | `FFFFFFFF ? FFFFFFFF` | idempotent |
| `02067D50 / E5842268` | `0x7d8 / 020EA1D8` | 4 / r2 | `00000000 ? 00000000` | idempotent |
| `02067D58 / E5840274` | `0x7e4 / 020EA1E4` | 4 / r0 | `00000000 ? 00000000` | idempotent |
| `02067D5C / E5842284` | `0x7f4 / 020EA1F4` | 4 / r2 | `00000000 ? 00000000` | idempotent |
| `0202602C / E58707F4` | `0x7f4 / 020EA1F4` | 4 / r0 | `00000000 ? 00000001` | value-changing |
| `02026034 / E58707C8` | `0x7c8 / 020EA1C8` | 4 / r0 | `00000000 ? 00080000` | value-changing |
| `02026040 / E58717CC` | `0x7cc / 020EA1CC` | 4 / r1 | `00000000 ? 00060000` | value-changing |

The transient +7CC zeroing/restoration creates two value-changing events while leaving its final value equal to AO. Idempotent stores remain real architectural events, not inferred omissions.

## CPU and full memory audit

Final r0?r12=`020E9F70,00060000,0,1,020E9A00,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B0C`, LR=`02067C58`, PC=`02026044`, NZCV=`0000`; T=0, mode31, I=F=0. All intermediate states match AP.

| Register | AO before | AQ after |
|---|---|---|
| r0 | `0x02132750` | `0x020E9F70` |
| r1 | `0x02131D24` | `0x00060000` |
| r3 | `0x0000001F` | `0x00000001` |
| r4 | `0x020E9F70` | `0x020E9A00` |
| SP | `0x027E3B04` | `0x027E3B0C` |
| LR | `0x02026010` | `0x02067C58` |
| PC | `0x02067C48` | `0x02026044` |

NZCV changes1000?0000; intermediate0110/1000/0000 match AP. Unlisted terminal registers are unchanged.

| Changed RAM byte | AO | AQ |
|---|---|---|
| `0x020EA1BC` | `34` | `70` |
| `0x020EA1BD` | `A0` | `9F` |
| `0x020EA1C9` | `D0` | `00` |
| `0x020EA1CA` | `02` | `08` |
| `0x020EA1F4` | `00` | `01` |

**Exactly5 main-RAM bytes change; DTCM changes0 bytes.** All other4MiB RAM and16KiB DTCM bytes are audited. Main-RAM SHA256 before=`541991ee1d577324f15893effad69140c1aa0e2d7aeb3a8d302eabbae01e24bd`, after=`84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340`. DTCM before=after=`1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716`.

| Audited exercise field | Before | After |
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
| 0x7bc | `020EA034` | `020E9F70` |
| 0x7e8 | `00000000` | `00000000` |
| 0x7c8 | `0002D000` | `00080000` |
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
| 0x7f4 | `00000000` | `00000001` |
| 0x610 | `00000000` | `00000000` |

Phase/delay/count/result flag remain1/1/1/1; +7C0 remains02132750, +7C4 remains0. Only final fields +7BC,+7C8,+7F4 differ. No extra score/count/phase/history or state mutation outside these certified writes; video/touch/scene owners unchanged. Gameplay has not resumed. No general result-completion/progression meaning is claimed for the offset-only helper fields.

Save before=after SHA256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; changed bytes0, logical requests0, Flash commits0, dirtyfalse. Source checkpoint/save remain immutable. MMIO accesses0: the exact bus ledger contains only certified main-RAM code/object/literal and DTCM stack reads and object writes.

## Accounting and forbidden boundary

| Counter | Before | After | Delta |
|---|---|---|
| insn9 | 281097945 | 281097990 | 45 |
| cycle9 | 3416875553 | 3416875664 | 111 |
| insn7 | 96026779 | 96026779 | 0 |
| cycle7 | 1708437767 | 1708437825 | 58 |

ARM7 cycles advance58 while ARM7 instructions remain0; counters are reported as observed, never restored/synthesized. No scheduler redesign or frozen-all-accounting claim.

**Pending `02026044 / EB01053C / BL0206753C` was not fetched by the interpreter, dispatched or executed.** The complete51-read ledger has no terminal fetch. Terminal opcode validation uses debug reads only. The pre-call ABI is r0?r3=`020E9F70,60000,0,1`, SP=`027E3B0C`, incoming LR=`02067C58`; dispatch would set LR02026048. No target instruction at0206753C ran.

## Focused validation and reproduction

Six focused groups pass: AQ?s1400 full-state/path/opcode/budget/read/write assertions; AO?s11 guard assertions; existing publication policy; hook ordering/single underlying bus call; production source identity; compiled certificate reproducibility. Build succeeds with existing Task S indentation warnings only. Disabled control, authoritative replay and exhaustive audit pass with clean exits and no forced cleanup.

```powershell
python tools/task_aq/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_aq/build.ps1
python tools/task_aq/check.py
python tools/task_aq/run.py --out local/task-aq/disabled-repro --disabled --port 20501
python tools/task_aq/run.py --out local/task-aq/session-repro --port 20502
python tools/task_aq/analyze.py --out local/task-aq/session-repro --disabled local/task-aq/disabled-repro --export local/task-aq/repro-result.json
```

Fresh output directories are required. Raw checkpoint/RAM/save/window/log evidence remains ignored under local/task-aq. Only ROM-free helpers, static proof tables and report/JSON are committed. Source ROM, generated binaries/C, save/state/assets are not committed. Unrelated jarvis-inbox-v1.zip remains untouched.

Next smallest recommendation: a separately authorized read-only static bounding of `02026044 ->0206753C` from this exact ABI. The callee is not certified safe: large stack allocation and nested calls remain unbounded here. **No successor task started; stopped after AQ.**
