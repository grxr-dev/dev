# Task AO ? second value-changing object store

**FULL PASS.** Reconstructed and independently revalidated AN, then dispatched only `0x02067C44 / E5840250 / STR r0,[r4,#0x250]` for AO. Halted at `0x02067C48` before successor dispatch. [Machine-readable evidence](BrainAge_TaskAO_Result.json).

## Provenance and reconstruction

AN `0f3d697861a8d52f569ec051915258e02915d878`, AM `cb2126cfa0c2e75714b993cdc0124c49c8e1b680`, AL `7fe0ee8abba3ff487971c1ff4fb4ab6a45775e70`; branch `codex/brainage`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; framework baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`.

Preflight runs AN's immutable predecessor certificate and verifies committed AN reports/helpers, retained RAM/DTCM/save hashes and ordinal. Existing deterministic Task G checkpoint restore and frozen Task Y SDL input reconstruct the entire prefix without fabricated guest state. All **111** retained AN pre-dispatch CPU/opcode/ordinal observations match exactly. The 22 AN bus reads and earlier AK writes also match committed evidence.

At AO arming, runtime checks all16 registers, full flags/T/mode/masks, original opcode, complete4MiB main RAM and16KiB DTCM hashes, clean save identity, pending operands and instruction/cycle counters. Main RAM SHA-256 `9f31cfc87f6d2913f83bd98854c4837330dfdef539888c935f6b83aea0688dc9`; DTCM `1a17bcc82ed4e8bd5f03d70a1bddaa38b6dee106f1b10e3286ee9f721e238716`; save `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`. Complete image identity covers all mapped fields, independently decoded by the auditor.

## Real architectural store

Actual observed memory path: **Interpreter::step ? RtBus::write32 ? bus_write_u32**. Before-bus firewall checks exact PC/opcode/address/width/source/before value/count/ordinal; after-bus hook verifies readback and records the event. The only AO bus read is its one instruction fetch. Unknown/repeated/MMIO reads and every other write are rejected before underlying bus access.

| Property | Observed |
|---|---|
| PC / opcode | `02067C44 / E5840250` |
| Base / offset | r4=`020E9F70`, immediate=`250` |
| Target | `020EA1C0`, exercise+`7C0` |
| Width / source | 4 bytes, r0=`02132750` |
| Before / after | `02133A18 ? 02132750` |
| Architectural writes attributable to AO | **1** |
| AO dispatches | **1** |
| Terminal PC | `02067C48`, **not dispatched** |

The control hook precedes bank handoff, instruction accounting, fetch and Interpreter::step. Exact index110/ordinal281097944 permits only the pending STR. Index111/ordinal281097945 accepts terminal observation only, checks complete post-state and halts/unwinds; no successor or later guest instruction executes.

## CPU, memory, fields and persistence

Final r0-r12 (hex): `02132750,02131D24,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`; SP=`027E3B04`, LR=`02026010`, PC=`02067C48`. **Only PC changes**, `02067C44 ? 02067C48`. NZCV=`1/0/0/0`, T=0, System mode31, I=F=0, all unchanged.

Complete main RAM comparison finds **two changed bytes**: `020EA1C0:18?50`, `020EA1C1:3A?27`. The retained little-endian word changes `18 3A 13 02 ? 50 27 13 02`. No other RAM/global/object write occurs. DTCM is byte-identical to AN, **zero changed bytes**. Write-event count is audited independently from resulting byte differences.

All field values below are hexadecimal; unknown fields retain offset-only descriptions.

| Exercise offset | Before | After |
|---|---|---|
| 0x10 | 0x1 | 0x1 |
| 0x20 | 0x1 | 0x1 |
| 0x34 | 0xda | 0xda |
| 0x44 | 0x1 | 0x1 |
| 0x1C | 0x0 | 0x0 |
| 0x3C | 0x14 | 0x14 |
| 0x40 | 0x1 | 0x1 |
| 0x58 | 0xb | 0xb |
| 0x4C | 0x4 | 0x4 |
| 0x504 | 0x1 | 0x1 |
| 0x51C | 0xff | 0xff |
| 0x38 | 0x0 | 0x0 |
| 0x50c | 0xff | 0xff |
| 0x514 | 0x4 | 0x4 |
| 0x7c4 | 0x0 | 0x0 |
| 0x630 | 0x1 | 0x1 |
| 0x5f0 | 0x44 | 0x44 |
| 0x5d0 | 0x2131d24 | 0x2131d24 |
| 0x7c0 | 0x2133a18 | 0x2132750 |
| 0x7bc | 0x20ea034 | 0x20ea034 |
| 0x7e8 | 0x0 | 0x0 |
| 0x7c8 | 0x2d000 | 0x2d000 |
| 0x7cc | 0x60000 | 0x60000 |
| 0x7d0 | 0x1000 | 0x1000 |
| 0x7d4 | 0x1000 | 0x1000 |
| 0x7f8 | 0x0 | 0x0 |
| 0x7dc | 0x0 | 0x0 |
| 0x7e0 | 0x0 | 0x0 |
| 0x7fa | 0xffff | 0xffff |
| 0x7ec | 0x0 | 0x0 |
| 0x7f0 | 0xffffffff | 0xffffffff |
| 0x7d8 | 0x0 | 0x0 |
| 0x7e4 | 0x0 | 0x0 |
| 0x7f4 | 0x0 | 0x0 |

Save is byte-identical and clean; changed bytes **0**, logical save requests **0**, Flash commits **0**. MMIO accesses **0**. Video/touch/scene/ownership observations remain unchanged. No additional score/count/phase/progression/history/result-completion/gameplay-resume effect beyond the isolated store. No data at the newly stored value is dereferenced. The semantic role of +7C0 remains **unproven**.

ARM9 ordinal **281097944 ? 281097945 (+1)**; cycles **3416875550 ? 3416875553 (+3)**. ARM7 ordinal **96026779 ? 96026779 (0)**; cycles **1708437767 ? 1708437767 (0)**. Counters are observed, never restored or synthesized. AN's earlier ARM7 cycle advance is outside AO.

## Validation and reproduction

Four focused groups pass: 11 AO dispatch/store guard assertions, predecessor AN guard negatives, unchanged publication policy tests, hook ordering and one underlying bus call per access. Production host/service/exercise/policy sources match AN. Build passes with pre-existing historical Task S indentation warnings only. Disabled control exits before input/publication with zero RAM/save change; enabled bounded replay and exhaustive audit pass, both with clean exit and no forced cleanup. No broad gameplay or validation matrix ran.

```powershell
python tools/task_ao/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_ao/build.ps1
python tools/task_ao/check.py
python tools/task_ao/run.py --out local/task-ao/disabled-repro --disabled --port 20301
python tools/task_ao/run.py --out local/task-ao/session-repro --port 20302
python tools/task_ao/analyze.py --out local/task-ao/session-repro --disabled local/task-ao/disabled-repro --export local/task-ao/repro-result.json
```

Fresh output directories are required. Raw state/RAM/save/log/window evidence stays ignored under `local/task-ao/`; only this report, JSON and focused `tools/task_ao/` helpers are committed. Installed opt-in diagnostic infrastructure remains ignored; production behavior, scheduler, ROM and generated ROM-derived C are unchanged. Unrelated existing work and `jarvis-inbox-v1.zip` are preserved.

Evidence is **forced Tier-3 exact-context original ARM interpreter; no compiled parity**. No higher-level field meaning, general gameplay behavior or helper return is established. Next smallest recommended task: read-only audit of successor `0x02067C48` and its smallest safe boundary. **Task AP not started.**
