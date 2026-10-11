# Task AI - single MOV and inner-call boundary

**FULL PASS.** A fresh frozen real-SDL replay reconstructs the exact authoritative AH stop. Exactly **0x02026250 / E1A00004 / MOV r0,r4** executes in AI. The runner halts at **0x02026254 / EBFFFF47 before dispatch of BL 0x02025F78**. No later instruction executes and no compiled parity is claimed.

AH: `2b846d5ddeb751c59f02caa1aacd227d016a9b24`; AG: `e2bc0765d9d70f8d3e8b12dbc7fbf5c42ac3b5a5`. Branch `codex/brainage`. [Result JSON](BrainAge_TaskAI_Result.json).

## Exact reconstruction and fail-closed gate

ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Preflight validates committed AH reports/helpers and retained CPU/RAM/DTCM/save evidence, with predecessor AG/AF/AE validation. All original files remain unchanged. The live pre-MOV gate checks every r0-r15, NZCV/T/mode/I/F, exact opcode and ordinal, complete main RAM/DTCM/save hashes and mapped fields through image equality.

The existing immutable Task G checkpoint and frozen Task Y input are replayed via ten real SDL events/native touch ownership. Recognition remains 2 -> 4, with no custom guest touch deliveries. No guest state is fabricated at the AH boundary. All **65 AH pre-dispatch observations** match retained AH exactly: PCs/opcodes, complete reported CPU state and ordinals. The reconstructed predecessor STR produces the same real RtBus write event, but this occurs before AI and is not an AI write.

The fixed allowlist has 66 observations / 65 dispatches including reconstruction. AI starts at decision index 64 and dispatches exactly one MOV. Index 65 is terminal-only; wrong PC, repeated entry, ordinal mismatch, opcode/register/flags divergence or later entry fails before dispatch. The halt hook precedes bank handoff, instruction increment, fetch and Interpreter::step. Every interpreter write is rejected while AI is armed; interpreter reads reject non-main-RAM/MMIO access. The hooks are task-local opt-in; underlying bus calls remain once, without a scheduler refactor or generated C change.

## CPU and side effects

Only these register deltas occur from AH:

| Register | Before | After |
|---|---|---|
| r0 | 000000DA | 020E9A00 |
| PC | 02026250 | 02026254 |

Final r0-r12 (hex): `020E9A00, 00000001, 00000004, 00000000, 020E9A00, 00000000, 00000072, 00000000, 020E9A00, 00000000, 00000000, 00000000, 00000000`. SP=`027E3B2C`; LR=`02026B94`; PC=`02026254`. NZCV remains `1/0/0/0`; T=0, System mode=31, I=F=0. r1-r14 and all audited flags are unchanged.

Main RAM: **0 byte differences across 4 MiB**. DTCM: **0 byte differences across 16 KiB**. AI write events **0**; the one reconstructed AH write remains outside the AI window.

| Image | Before and after SHA-256 |
|---|---|
| Main RAM | `b987e4950b03b3621ffd5c47e715150240c54913f94652149edec23424950ce9` |
| DTCM | `ffebd1000bf8222fd3b1224bfed4f6596f4288e38b82d6c22b1aa6c14bc37547` |
| Save | `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb` |

All mapped fields remain identical (decimal except +34):

| Offset | Before | After |
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

Save changed bytes **0**; logical save requests **0**; Flash commits **0**; dirty=false. Source checkpoint/save unchanged. AI MMIO accesses **0**, inner calls **0**, and no peripheral/gameplay/count/phase/progression/history/result-completion effect. Full exercise/manager/slot images and video/touch/scene observations remain unchanged. No claim that all normal scheduler bookkeeping is frozen.

## Accounting and checks

| Counter | Before | After | Delta |
|---|---|---|---|
| ARM9 instructions | 281097898 | 281097899 | 1 |
| ARM9 cycles | 3416875450 | 3416875451 | 1 |
| ARM7 instructions | 96026779 | 96026779 | 0 |
| ARM7 cycles | 1708437703 | 1708437703 | 0 |

No counters restored or unrelated scheduler investigation. Enabled/disabled fresh runs exit 0 without forced cleanup. Disabled control has no input/publication or RAM/save differences.

Focused checks pass: AI and predecessor AH guards; every opcode/register/PC/ordinal negative case; terminal BL rejection at all indices; frozen publication policy; unchanged custom production sources; pre-dispatch ordering; actual bus-hook order with exactly one underlying call per width; all writes forbidden and MMIO-read gate during AI. Offline audit checks full input/private isolation, complete AH prefix, start/terminal states, mapped fields, RAM/DTCM/save, write-event placement and exact accounting. Build passed with only existing historical Task S warnings. A task-local predecessor-prefix test length was corrected before any guest replay.

## Reproduction and limits

Only `tools/task_ai/` and these report/result files are committed. ROM/database bytes, local RAM/checkpoint/save dumps, screenshots/assets, BIOS/firmware, binaries and generated recomp-C are not committed. Runner SHA-256 `9290c5c7fa8ce5ff44be5f818e60ddd8abddbac81250c3cafb202e0782d801fd`.

```powershell
python tools/task_ai/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ai/build.ps1
python tools/task_ai/check.py
python tools/task_ai/run.py --out local/task-ai/disabled-FRESH --disabled --port 19981
python tools/task_ai/run.py --out local/task-ai/session-FRESH --port 19982
python tools/task_ai/analyze.py --out local/task-ai/session-FRESH --disabled local/task-ai/disabled-FRESH --export docs/BrainAge_TaskAI_Result.json
```

Fresh output directories must not exist. To audit retained evidence, run check/analyze with `local/task-ai/session-001` and `disabled-001` before another build replaces the executable hash.

Evidence tier: **forced Tier-3 exact-context original ARM interpreter**, one frozen 11 - 7 / recognized-4 context. No compiled parity, inner-routine safety, full routine return or gameplay completion claim.

Next smallest recommended task: a **read-only exact-state audit** of the pending inner BL arguments and minimum first-instruction boundary before proposing any separately authorized dynamic call. **Stopped after AI; AJ not started.**
