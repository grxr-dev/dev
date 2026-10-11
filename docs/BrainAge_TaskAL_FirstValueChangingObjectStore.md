# Task AL ? first value-changing object store

**FULL PASS.** Reconstructed and revalidated the authoritative AK stop, dispatched only `0x02067BDC / E5842254` (`STR r2,[r4,#0x254]`) for AL, then halted at `0x02067BE0` before successor dispatch. [Complete machine-readable audit](BrainAge_TaskAL_Result.json).

## Provenance and guards

AK commit `dd29b71e182611fb73016aa1a13367e70c9cd290`; AJ commit `a1d2c76baedc0ae841086eeccaf9aa5daebe8d16`. ROM SHA-1 `b8a105bacc3234dede8d4465df0869f2b922a0e2`; ndsrecomp baseline `3a57236bb23d25dcb4caad7d58d733311062ff5e`; branch `codex/brainage`.

Preflight revalidates committed AK/AJ sources, predecessor provenance, exact ROM/checkpoint identity and retained AK RAM/DTCM/save hashes. Existing fixed SDL/input reconstruction machinery restores the original Task G checkpoint and reproduces the complete AI/AK instruction prefix; it does not fabricate CPU/object state. All 91 pre-dispatch observations through AK match the retained authoritative AK trace exactly.

Before AL dispatch, runtime gates require all 16 registers, full NZCV/T/mode/interrupt masks, exact opcode, complete RAM/DTCM/save identity, eight reconstructed AK stack writes and actual ordinal/cycles. ARM9 ordinal is `281097924`. The opt-in control hook precedes instruction accounting, fetch and `Interpreter::step`. The only permitted AL interpreter read is the fixed 32-bit instruction fetch. Before-bus and after-bus hooks allow precisely one fixed 32-bit write, reject wrong PC/address/width/source/count/ordinal before bus dispatch, and verify readback. The terminal guard permits observation at `02067BE0` but forbids dispatch and any subsequent instruction.

## Explicit store proof

Actual path: `Interpreter::step ? RtBus::write32 ? bus_write_u32`.

| Property | Observed |
|---|---|
| PC / opcode | `02067BDC / E5842254` |
| Base / offset | r4=`020E9F70`, immediate=`254` |
| Effective address | `020EA1C4`, exercise+`7C4` |
| Width / source | 4 bytes, r2=`0` |
| Before / after word | `00000001 ? 00000000` |
| AL architectural writes | **1** |
| AL dispatches | **1** |
| Terminal successor | `02067BE0`, **not dispatched** |

## CPU, memory and effects

Final r0?r12 (hex): `020E9F70,0,0,1F,020E9F70,0,DA,020E9A00,020E9A00,0,0,0,0`. SP=`027E3B04`; LR=`02026010`; PC=`02067BE0`. Only PC changes `02067BDC ? 02067BE0`. NZCV=`0/0/1/0`; T=0, System mode=31, I=F=0, unchanged.

Full 4 MiB main RAM comparison finds exactly **one changed byte** at `020EA1C4`, `01 ? 00`; retained little-endian word is `00000001 ? 00000000`. No other object/global/RAM write occurs during AL. Complete 16 KiB DTCM is identical to AK, **zero changed bytes**. Write-event count and byte-diff count are independently measured.

| Exercise offset | Before ? after |
|---|---|
| +10 phase | 1 ? 1 |
| +1C | 0 ? 0 |
| +20 delay | 1 ? 1 |
| +34 | DA ? DA |
| +38 | 0 ? 0 |
| +3C | 20 ? 20 (decimal) |
| +40 | 1 ? 1 |
| +44 correct count | 1 ? 1 |
| +4C | 4 ? 4 |
| +58 | 11 ? 11 (decimal) |
| +504 result flag | 1 ? 1 |
| +50C | 255 ? 255 (decimal) |
| +514 | 4 ? 4 |
| +51C | 255 ? 255 (decimal) |
| +7C4 | **1 ? 0** |

Save remains byte-identical, SHA-256 `a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`; logical save requests **0**, Flash commits **0**, dirty=false. MMIO accesses **0**. Video/touch/scene/ownership observations remain unchanged. No additional score/count/phase/progression/history/result-completion/gameplay-resume effect beyond the isolated mechanically proven mutation. The semantic role of +7C4 is **unproven**.

ARM9 ordinal `281097924 ? 281097925` (**+1**); cycles `3416875512 ? 3416875515` (**+3**). ARM7 ordinal `96026779 ? 96026779`, cycles `1708437703 ? 1708437703` (**0/0**). Counters are observed, never synthesized/restored.

## Validation and reproduction

Four focused groups pass: 11 AL positive/negative guard assertions, predecessor AK guard negatives, unchanged publication policy tests, and hook ordering/single underlying bus call per width. Runner build passes with only pre-existing Task S indentation warnings. Disabled control has no input/publication, zero RAM/save change and clean exit. Enabled replay and exhaustive prefix/CPU/image/event audit pass.

```powershell
python tools/task_al/preflight.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_al/build.ps1
python tools/task_al/check.py
python tools/task_al/run.py --out local/task-al/disabled-repro --disabled --port 20101
python tools/task_al/run.py --out local/task-al/session-repro --port 20102
python tools/task_al/analyze.py --out local/task-al/session-repro --disabled local/task-al/disabled-repro --export local/task-al/repro-result.json
```

Use fresh output directories. Raw checkpoint/RAM/save/log/window evidence stays ignored under `local/task-al/`; no ROM bytes, assets, binaries or generated C are committed. Production custom sources, scheduler and guest ROM are unchanged. Unrelated existing files are preserved.

Evidence remains **forced Tier-3 exact-context original ARM interpreter; no compiled parity**. This proves only the isolated store in this frozen context, not its semantic purpose or later helper behavior. Next smallest recommended task: read-only audit of the successor at `0x02067BE0` and its smallest safe boundary. **Task AM not started.**
