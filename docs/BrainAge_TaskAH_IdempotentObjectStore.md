# Task AH - dynamic audit of the idempotent object store

**FULL PASS.** A fresh frozen SDL replay reconstructed and revalidated the authoritative AG stop. Exactly one additional original ARM instruction executed, with a positively observed interpreter write event despite zero changed bytes. Execution halted at **0x02026250 before dispatch**. No compiled parity is claimed.

AG: `e2bc0765d9d70f8d3e8b12dbc7fbf5c42ac3b5a5`; AF: `63ff0c59f995fe9e2df57248ef261d1f4c8c6819`; AE: `6a43d5bfa4c85773b0f986b9d73944ab5e01700e`. Branch `codex/brainage`. [Result JSON](BrainAge_TaskAH_Result.json).

## Identity and exact AG reconstruction

ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Preflight compares the committed AG reports and tools, retained full RAM/DTCM hashes, expected complete CPU state, and STR/successor opcodes. AG/AF/AE files and custom production sources remain unchanged.

The driver reuses AG machinery, immutable Task G checkpoint and frozen Task Y input through ten real SDL events and native touch ownership. Recognition is 2 -> 4; custom guest touch deliveries are zero. No guest registers, checkpoint contents or CPU counters were fabricated/restored at the AH boundary. All 64 AG pre-dispatch observations match retained AG exactly, including registers, flags, instruction words and ordinals. The live boundary gate verifies AG RAM/DTCM/save hashes, all expected architectural registers, NZCV/T/mode/I/F, mapped fields through whole-image equality, exact code and instruction budget before arming the store.

## One dispatch and explicit write evidence

AH executed **0x0202624C / E5840034 / STR r0,[r4,#0x34]** only. The next observation is **0x02026250 / E1A00004**, terminal-only; MOV r0,r4 never dispatched. No inner BL at 0x02026254 or later guest instruction executes. The full reconstruction has 65 observations / 64 dispatches; its AH delta is one.

Task-local opt-in hooks bracket the real interpreter RtBus write methods. While AH is armed, writes fail before the underlying bus call unless ARM9, PC, opcode, address, width, source value and single-write count all match the authorized store. The underlying bus call remains exactly once; readback is checked after it. All interpreter read widths reject non-main-RAM/MMIO access during AH. Hooks return without effects when AH is unarmed or disabled.

The recorded event comes from `Interpreter::step -> RtBus::write32 -> bus_write_u32`:

| PC / opcode | Address | Width | Source | Before | After | Events |
|---|---|---|---|---|---|---|
| 0202624C / E5840034 | 020E9A34 | 4 bytes | r0 = 000000DA | 000000DA | 000000DA | 1 |

This is a write-path event, not an inference from memory equality. A second write or unexpected width/address/value fails closed. The terminal gate demands precisely one event before halting ahead of bank handoff, instruction increment/fetch and Interpreter::step.

## CPU and memory

Final r0-r12 (hex): `000000DA, 00000001, 00000004, 00000000, 020E9A00, 00000000, 00000072, 00000000, 020E9A00, 00000000, 00000000, 00000000, 00000000`.

SP=`027E3B2C`; LR=`02026B94`; PC=`02026250`; NZCV=`1/0/0/0`; T=0, System mode=31, I=F=0. The only register delta from AG is **PC 0202624C -> 02026250**. All r0-r14 and flags remain unchanged.

Main RAM: **0 changed bytes across 4 MiB**, separately from **1 write event**. DTCM: **0 changed bytes across 16 KiB**, byte-identical to AG, including its prior PUSH footprint.

RAM before/after SHA-256: `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9`. DTCM before/after SHA-256: `ffebd1000bf8222fd3b1224bfed4f6596f4288e38b82d6c22b1aa6c14bc37547`.

All mapped fields are unchanged (decimal values except +34 shown in hex):

| Exercise offset | Before | After |
|---|---|---|
| 0x10 | 1 | 1 |
| 0x20 | 1 | 1 |
| 0x34 | 0xDA | 0xDA |
| 0x44 | 1 | 1 |
| 0x1C | 0 | 0 |
| 0x3C | 20 | 20 |
| 0x40 | 1 | 1 |
| 0x58 | 11 | 11 |
| 0x4C | 4 | 4 |
| 0x504 | 1 | 1 |
| 0x51C | 255 | 255 |
| 0x38 | 0 | 0 |
| 0x50c | 255 | 255 |
| 0x514 | 4 | 4 |
| 0x7c4 | 1 | 1 |

No score/count/phase/progression/history/result-completion or gameplay-resume effect: complete RAM, exercise, manager and slot images are unchanged from AG. The +34 semantic role remains unproven.

## Persistence, accounting and validation

Save byte-identical, zero changed bytes; SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`. Logical save requests **0**, Flash commits **0**, dirty=false. No AH MMIO accesses or peripheral effects; guest video/touch/scene observations are unchanged. Source checkpoint and source save remain unchanged.

| Accounting | Before | After | Delta |
|---|---|---|---|
| ARM9 instructions | 281097897 | 281097898 | +1 |
| ARM9 cycles | 3416875447 | 3416875450 | +3 |
| ARM7 instructions | 96026779 | 96026779 | 0 |
| ARM7 cycles | 1708437703 | 1708437703 | 0 |

No unrelated scheduler investigation/refactor or counter restoration. Both fresh enabled/disabled runners exit 0 without forced cleanup. Disabled control has no input/publication or RAM/save changes.

Focused checks passed: AH/AG guard positive and negative PC/ordinal/opcode/every-register cases; store width/address/value/PC/opcode negatives; terminal/inner-call rejection; unchanged production source and publication policy; actual bus-hook ordering and single underlying calls; pre-dispatch hook ordering. Offline analysis audits all original input/isolation/persistence checks, exact AG prefix, store event order, final CPU, all memory bytes, mapped fields and accounting. Build passed with existing historical Task S warnings only.

## Artifacts and limits

Only this report/result and `tools/task_ah/` are committed. ROM/database bytes, checkpoint/RAM/save dumps, assets/screenshots, BIOS/firmware, binaries and generated C remain local and uncommitted. Runner SHA-256 `890773e28ab85d03c3aec732afd40703404f7ae81d799842a4424d84eb323e8b`.

Evidence tier: **forced Tier-3 exact-context original ARM interpreter**, one frozen 11 - 7 / recognized-4 context with actual Bus write-event proof. No compiled parity, full routine/gameplay completion or semantic identification of +34. Interpreter-access attribution and unchanged peripheral observations do not claim all normal scheduler bookkeeping is frozen.

Retained evidence audit (run before another build replaces the runner hash):

```powershell
python tools/task_ah/preflight.py
python tools/task_ah/check.py
python tools/task_ah/analyze.py --out local/task-ah/session-001 --disabled local/task-ah/disabled-001 --export docs/BrainAge_TaskAH_Result.json
```

Separately authorized fresh reproduction: preflight, `powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ah/build.ps1`, check, then `python tools/task_ah/run.py --out local/task-ah/disabled-FRESH --disabled --port 19971` and `python tools/task_ah/run.py --out local/task-ah/session-FRESH --port 19972`; audit/export those paths. Output directories must not exist.

Next smallest task, only if authorized: audit exactly **MOV r0,r4 at 0x02026250**, halt before **0x02026254**, and continue to forbid the inner BL. **Stopped after AH; AI not started.**
