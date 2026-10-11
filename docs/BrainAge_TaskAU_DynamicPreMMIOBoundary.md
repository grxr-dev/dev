# Task AU - dynamic pre-MMIO boundary

**FULL PASS.** Reconstructed the exact AS stop, executed AT's certified seven original ARM instructions, and halted at `02001980` before interpreter fetch/accounting/dispatch of `E1C130B0 / STRH r3,[r1]`. Exactly one DTCM word write occurred; two DTCM bytes changed. Main RAM, all 35 mapped fields and save are unchanged. No MMIO access occurred.

AT `6478bd11b386799a3f4e03f923c39227e982c51d`; AS `72c93f2eb0a561ff4b047d171e904477d8553e7b`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`. Forced Tier-3 exact-context original ARM interpreter evidence only; no compiled parity.

## Reconstruction and guards

Preflight verifies committed AT/AS artifacts, predecessor provenance, exact ROM/checkpoint/save identity, retained full AS RAM/DTCM/save hashes, and AT's independently decoded certificate with 11 static negative checks. The entire validated causal replay is retained: 112 earlier decision observations, 46 AQ observations and 12 AS observations, with all predecessor access ledgers, match their authoritative runs exactly. Frozen real SDL frontend input remains identical; the isolated recognizer returns 2 then 4 and tears down before publication. No CPU/checkpoint state is fabricated.

Before arming AU, the full AS CPU/flags/mode/masks, ordinal and cycles, full 4 MiB RAM/16 KiB DTCM/save images, every certified code word, both literal values and the saved-LR before-word are checked. Full-image equality enforces all 35 field values. Every instruction observation checks all registers and flags, exact opcode/ordinal, ordered completed read/write counts and complete expected images.

The opt-in control is before bank handoff, instruction accounting, instruction fetch and Interpreter::step. Ordered RtBus guards reject unexpected reads/writes, addresses, widths, source values, opcodes and budget overrun before the original bus call. Unknown/MMIO addresses are rejected before diagnostic readback. There is exactly one underlying bus operation per adapter. Only a diagnostic expected-DTCM copy is updated. The final stop permits no interpreter fetch of the pending STRH; debug inspection of its code word is distinct from execution.

Pre-execution generator destination/schema and copied namespace issues were corrected before either guest run; no runtime divergence, broadened boundary, generated C edit or production-source change.

## Exact path and frame

| PC / opcode | Independently certified decode | Effect |
|---|---|---|
| `0x02067564 / 0xEBFE692A` | `bl #0x2001a14` | BL creates LR; enters wrapper |
| `0x02001A14 / 0xE92D4000` | `stmdb sp!, {lr}` | DTCM [027E3658] := LR=02067568 |
| `0x02001A18 / 0xE24DD004` | `sub sp, sp, #4` | allocate 4 bytes; no initialization |
| `0x02001A1C / 0xEBFFFFD4` | `bl #0x2001974` | BL enters divider setup leaf |
| `0x02001974 / 0xE59F1028` | `ldr r1, [pc, #0x28]` | r1 := main-RAM literal [020019A4] |
| `0x02001978 / 0xE3A03001` | `mov r3, #1` | r3 := 1 (idempotent register assignment) |
| `0x0200197C / 0xE59F2024` | `ldr r2, [pc, #0x24]` | r2 := main-RAM literal [020019A8] |

Outer BL targets `02001A14` and creates LR `02067568`. STMDB SP!,{LR} saves it at `027E3658` and decreases SP by four; SUB reserves four more bytes, for eight bytes total (`027E365C -> 027E3654`). The setup BL targets `02001974` and creates LR `02001A20`. No return occurs. The literal loads set r1=`04000280`, r2=`04000290`; they read main-RAM literals, not hardware.

## Actual bus ledger and memory

The actual interpreter bus write at `02001A14 / E92D4000` is Write32 `[027E3658]`, source r14/LR=`02067568`, immediate before `02067AE0`, actual after `02067568`. It matches AT exactly. One value-changing architectural write, zero idempotent writes; do not infer this event from the byte diff.

| Changed DTCM byte | Before | After |
|---|---|---|
| `027E3658` | `E0` | `68` |
| `027E3659` | `7A` | `75` |

The complete 16 KiB DTCM diff contains only those two bytes. Main RAM has zero changed bytes.

| Image | SHA-256 before | SHA-256 after |
|---|---|---|
| mainram | `84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340` | `84190cc68ea67b735c89cadbc52b9ab985eec8a9e31ba0ee9851b101a9e2c340` |
| dtcm | `48b89027a274b3268219cdc6a8cd1f7fe15bf442a78b3931d79c4e6ae3ea36e4` | `a5313aa2084674d767307c09ebd86fb888ebf992b8f486602412f9499c55496f` |

Nine actual reads comprise seven instruction fetches and two literal Read32 events: `02001974 -> [020019A4]=04000280`, `0200197C -> [020019A8]=04000290`. Their order interleaved with the one write is audited, including intermediate CPU states. No reads or writes touch MMIO.

## CPU and mapped state

Final r0-r12=`1000,04000280,04000290,1,020EA1BC,0,DA,020E9A00,1000,1000,020FD00C,0,48C`; SP=`027E3654`, LR=`02001A20`, PC=`02001980`, NZCV=`0000`, T/mode/I/F=0/31/0/0.

| Register delta | AS before | AU after |
|---|---|---|
| r1 | `0x02132750` | `0x04000280` |
| r2 | `0x00000000` | `0x04000290` |
| SP | `0x027E365C` | `0x027E3654` |
| LR | `0x02026048` | `0x02001A20` |
| PC | `0x02067564` | `0x02001980` |

All unlisted registers and flags remain unchanged.

| Exercise offset | Before | After |
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

All 35 fields remain unchanged; phase/delay/count/result flag stay `1/1/1/1`, +7BC=`020E9F70`, +7C0=`02132750`, +7C4=0, +7C8=`80000`, +7CC=`60000`, +7F4=1. Complete main-RAM equality excludes new object/global/score/progression/history/result-completion changes. Gameplay does not resume; video/touch/scene/native-owner state stays unchanged.

Save before=after SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; changed bytes=0, logical save requests=0, Flash commits=0, dirty=false. Disabled and authoritative initial/session/final saves are byte-identical. Source checkpoint/save remain immutable. MMIO ledger is empty.

## Accounting and forbidden next effect

| Counter | Before | After | Delta |
|---|---|---|
| insn9 | 281098001 | 281098008 | 7 |
| cycle9 | 3416875700 | 3416875721 | 21 |
| insn7 | 96026779 | 96026779 | 0 |
| cycle7 | 1708437825 | 1708437825 | 0 |

`02001980 / E1C130B0` was **not fetched by the interpreter, dispatched or executed**. The nine-read ledger excludes its fetch; terminal observation is before accounting. No later instruction executes. Terminal r1=`04000280`, r3=1 implies a would-be Write16 of `0001` to divider control. This is inferred from registers and decoded operands only; no hardware address was read or written. AU proves no divider behavior, timed polling, or whole-call termination.

## Validation and reproduction

Eight focused groups pass: AU 237 positive/negative state/path/opcode/budget/read/write checks (including forbidden MMIO/fetch rejection); AS 404 predecessor checks; AO 11 checks; publication policy; hook order/single underlying bus call; exact AS/AQ table reuse; production-source identity; table reproducibility. Build passes with existing Task S indentation warnings only. Disabled control exits without input/publication or RAM/save changes. The authoritative run exits cleanly at the boundary without forced cleanup; exhaustive CPU/access/image/save audit passes.

```powershell
python tools/task_au/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_au/build.ps1
python tools/task_au/check.py
python tools/task_au/run.py --out local/task-au/disabled-repro --disabled --port 20701
python tools/task_au/run.py --out local/task-au/session-repro --port 20702
python tools/task_au/analyze.py --out local/task-au/session-repro --disabled local/task-au/disabled-repro --export local/task-au/repro-result.json
```

Use fresh output directories. Authoritative ignored local evidence is in `local/task-au/session-001`, disabled control in `local/task-au/disabled-001`. Only ROM-free helpers/proof constants/report/JSON are committed; no ROM, checkpoints/saves/dumps, game assets, generated C/binaries or BIOS. Unrelated `jarvis-inbox-v1.zip` remains untouched.

Next smallest task: separately authorized static safety analysis of the pending divider Write16 and required modeled-time/polling boundary. Do not dynamically enter MMIO based on this setup proof. Stopped after AU; no successor task started.
