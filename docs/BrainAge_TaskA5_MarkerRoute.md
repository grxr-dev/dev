# Brain Age Task A.5: marker-route reconciliation

## Result and scope

`CLEAR-RAM-CHECK` was reproduced at cartridge Flash offset `0x180` by
selecting **Daily Training once** from the title/menu and letting its entry
initialization finish. No introductory dialogue was advanced, and no date,
handedness, profile question, Brain Age Check, or Stroop screen was reached.
Progression stopped at the first detected completed marker transaction.

The last pre-marker screenshot shows the Daily Training heading, Kawashima,
an empty speech bubble, Back, and a disabled More button. The post-marker
screenshot shows the same screen with the beginning of `Hello! My` in the
bubble. The intervening action was **wait only**, following the single menu
tap. This was entry initialization, not a second selection or setup answer.

Reconciliation: **A, for the tested fresh-save route**. Task A never selected
Daily Training. Its passive initialization zeroed this region instead of
writing the marker. The first 31,648 trace lines in this new session are
byte-identical to the preserved Task A checkpoint trace. Confidence is high
for the observed route and the reason that capture missed the marker; this
does not establish that no other menu route or unbounded passive wait could
ever produce it.

The historical phrase "ordinary fresh boot produces CLEAR-RAM-CHECK" is
inaccurate for the demonstrated passive-boot boundary. The historical
description of early Daily Training writes before date/handedness matches
the reproduced zeroed mirrored records followed by this marker. A generic
integrity/setup purpose remains an interpretation, not proof of save-format
semantics. No changed bytes are classified as profile data here.

## Unchanged baseline and preserved evidence

- Checkout: `C:\Users\rustg\Documents\Codex\Muse\dev`, branch `codex/brainage`.
- Task A source commit: `b6bcef4ef29e3205271de4127214005cc1b2e4c0`.
- ndsrecomp: `3a57236bb23d25dcb4caad7d58d733311062ff5e`, existing Task A diagnostic patch.
- Runner: `build/task-a-runner/nds_runner.exe`; no rebuild or trace changes.
- Configuration: `config/brainage_task_a.toml`, direct boot, FreeBIOS,
  generated firmware, identity MAC `02:00:00:00:00:01`, network off.
- ROM SHA-1 rechecked at launch:
  `b8a105bacc3234dede8d4465df0869f2b922a0e2`.
- Initial Flash: 262,144 bytes of `FF`; a new save, not a restored state.
- Existing `local/task-a/boot-003-interpreter/` and
  `local/task-a/boot-004-checkpoint/` were not changed.

## Checkpoints

All new evidence is under ignored `local/task-a5/route-001/`. Each completed
checkpoint has raw engine A/B PNGs, before/after saves, a transition JSONL,
debug requests/responses, and a summary. Cycles below are ARM9 cycles.

| Checkpoint | Action / visible state | Cycles after | Net changed bytes | Marker |
| --- | --- | ---: | ---: | --- |
| `00-passive-boot-complete` | No input; disclaimer / Nintendo Please wait | 450000208 | 28976 from erased | absent |
| `01-passive-wait` | Wait; training/research startup animation | 584001182 | 0 | absent |
| `02-menu-checkpoint` | Title/menu reached without input | 723593345 | 0 | absent |
| `03-daily-training-selected` | Tap raw touch `(144,96)`; entry fade | 790593443 | 0 | absent |
| `04-daily-entry-settle` | Wait; Daily Training empty speech bubble | 859794390 | 1200 | absent |
| `05-daily-introduction` | Wait only; opening greeting begins | 881645472 | 351 | present at `0x180` |
| `06-stopped-at-marker` | Zero guest cycles; terminate this runner | 881645472 | 0 | present |

One raw touch press was held for approximately 3 million ARM9 cycles then
released. No keys or other taps were used. Flash was searched over its full
256 KiB image after every trace batch, including each individual commit in
that batch. Execution batches requested 1 million ARM9 cycles; the existing
`run_cycles` transient early-return behavior was handled using `run_rounds`.
Consequently screenshots/checkpoints sample slightly after the exact commit;
the trace, not screenshot timing, identifies the first marker construction.
The final checkpoint is 440822737 ARM7 cycles, about 2.74 million cycles after
the completed marker transaction. There are no subsequent Flash commits.

Two helper-only interruptions are preserved, not overwritten: initial
`00-passive-boot/` hit lazy trace-file creation before the first write, then
continued the same session after that helper fix; `02-passive-title/` captured
the menu but optional savestate export returned
`savestate GPU3D command state is invalid`. The successful zero-cycle
`02-menu-checkpoint` recovered the Flash checkpoint. Savestate export is now
optional and errors are recorded without invalidating Flash evidence. No
savestate load, emulator workaround, or trace defect correction was used.

## Flash transitions

### Menu immediately before selection to marker

- SHA-256 before:
  `4dc99c631da1bc7acc93c1a1ee1b333d675916eab5dce451ef329aec607fcf76`.
- SHA-256 after:
  `f8310763e5c388ceeb82b520c20fcd88e35a3c93af14db7d3dcaebcec292ede0`.
- Net changed bytes: **1,551**; accepted byte commits: **1,552** in **33**
  writing transactions, sequences **31649..33200**.
- Complete changed ranges (inclusive): `0x180..0x18E`, plus
  `0x7000 + 0x40*i .. 0x702F + 0x40*i` for every `i=0..15`, and
  `0x27000 + 0x40*i .. 0x2702F + 0x40*i` for every `i=0..15`.
- Mirrored records: **yes**, 16 pairs separated by `0x20000`; each is a
  48-byte `FF` to `00` write. The intervening 16-byte gaps are unchanged.
  This accounts for 1,536 changed bytes before the marker transaction.
- Record transaction `1223 + 8*i`, `i=0..31`, has sequences
  `31649 + 48*i .. 31696 + 48*i`. The first 16 are the lower copy, the
  next 16 its upper mirror. Byte commit cycles span 402180321..436988245.
  Full per-transaction origins/times are in `marker-route-audit.json`.

### Immediately preceding checkpoint to first marker checkpoint

- SHA-256 before:
  `ac26fce5e672c84ec0fd8278309769372a75fb51803d00f5c5202e453d2903c5`.
- SHA-256 after: the same `f8310763...292ede0` above.
- Net changed bytes: **351**; 352 accepted commits, sequences **32849..33200**.
- Complete changed ranges (inclusive): `0x180..0x18E`, and
  `0x27000 + 0x40*i .. 0x2702F + 0x40*i` for every `i=9..15`.
- This finishes the last seven upper mirrored records (336 bytes) and writes
  the marker (15 changed bytes). Earlier checkpoint `04` captured the first
  25 records (1,200 bytes). These are two observation intervals within one
  automatic entry transition, not two different user actions.

## Exact causal marker construction

One Flash command transaction, **1481**, produces **16 separate byte commits**
at `0x180..0x18F`, not one atomic host write. The first 15 bytes spell
`CLEAR-RAM-CHECK`; the final NUL was already zero and does not change Flash.
Thus the ASCII marker ends at **0x18E**, not the earlier shorthand 0x18D.
Old bytes are 16 zeros; new hex is `434c4541522d52414d2d434845434b00`.

Common fields for every row:

- `command="0x0A"`, `status_before_latch_clear=2`, `length=1`,
  `wrap_mask=262143`, `commit_path="flash_spi_write"`.
- Command and byte origins are both `valid=true`, **ARM7**, guest
  **PC `0x038032B8`**, `thumb=false`, `execution="tier3"`.
- Command-origin CPU/system cycle: **438080559**; instruction ordinal:
  **121362881**. This captured command origin is carried through SPI state.
- The actual byte origins are captured at the guest SPI stores, not sampled
  from an unrelated PC in the final host helper. CPU and system cycles are
  equal for ARM7. The existing verified instruction is `STRH r2,[r1]`.
- All 1,552 entry commits have those same core/PC/mode/path origins; none
  are ARM9 or unknown. No higher-level caller attribution is claimed.

| Sequence | Offset | Old -> new | SPI position | Byte CPU/system cycle | Byte instruction | Last |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 33185 | 0x180 | 00 -> 43 | 4 | 438081084 | 121363145 | false |
| 33186 | 0x181 | 00 -> 4C | 5 | 438081204 | 121363204 | false |
| 33187 | 0x182 | 00 -> 45 | 6 | 438081324 | 121363263 | false |
| 33188 | 0x183 | 00 -> 41 | 7 | 438081444 | 121363322 | false |
| 33189 | 0x184 | 00 -> 52 | 8 | 438081564 | 121363381 | false |
| 33190 | 0x185 | 00 -> 2D | 9 | 438081684 | 121363440 | false |
| 33191 | 0x186 | 00 -> 52 | 10 | 438081804 | 121363499 | false |
| 33192 | 0x187 | 00 -> 41 | 11 | 438081924 | 121363558 | false |
| 33193 | 0x188 | 00 -> 4D | 12 | 438082044 | 121363617 | false |
| 33194 | 0x189 | 00 -> 2D | 13 | 438082164 | 121363676 | false |
| 33195 | 0x18A | 00 -> 43 | 14 | 438082284 | 121363735 | false |
| 33196 | 0x18B | 00 -> 48 | 15 | 438082404 | 121363794 | false |
| 33197 | 0x18C | 00 -> 45 | 16 | 438082524 | 121363853 | false |
| 33198 | 0x18D | 00 -> 43 | 17 | 438082644 | 121363912 | false |
| 33199 | 0x18E | 00 -> 4B | 18 | 438082764 | 121363971 | false |
| 33200 | 0x18F | 00 -> 00 | 19 | 438082885 | 121364030 | true |

Sequence **33199** first makes the full marker present. Sequence **33200**
finishes the transaction. Exact original JSON events are preserved locally
in `marker-transaction.jsonl`; the table plus common fields losslessly
describes their causal and byte data.

## Verification, artifacts, and reproducible commands

Independent replay from an erased image validates every logged old byte,
sequence, length, and change count and exactly reproduces the persisted save.
The entire run has 33,200 accepted commits, 209 writing transactions, and
30,527 cumulative changed-byte commits (not a net save-difference count).
Trace SHA-256:
`76eaf80dbffbe400daa53ddb00767519247a84a3ffcd7a554d2dece9a1854721`.
The full save contains exactly one marker.

New ROM-free files only:

- `tools/task_a/route_marker.py`: persistent single-session, one-action
  checkpoint helper; refuses further progression once a marker is found.
- `tools/task_a/analyze_marker_route.py`: independent replay, complete entry
  diff, first-marker detection, and extraction of its original transaction.
- This document. Task A instrumentation and configuration are unchanged.

Local-only outputs:

- `local/task-a5/route-001/flash.jsonl`, `erased.sav`, `ledger.sav`,
  `session.json`, `stdout.log`, `stderr.log`.
- Checkpoint directories listed above; PNGs, saves, optional states, JSON
  summaries, transition logs, and raw debug responses remain ignored.
- `marker-transaction.jsonl`, `marker-route-audit.json`, `trace-audit.json`,
  `initial-page-sequence.json` beneath that same root.
- Existing build and Task A paths are unchanged. The session's own process
  was terminated after capture. No runner was left progressing.

From the dev root, using an unused output directory (each checkpoint label
must also be new):

```powershell
$out = 'local/task-a5/route-NEW'
python tools/task_a/route_marker.py --out $out --label 00-boot --start --runner build/task-a-runner/nds_runner.exe --rom '..\Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' --cycles 450000000
python tools/task_a/route_marker.py --out $out --label 01-startup --cycles 134000000
python tools/task_a/route_marker.py --out $out --label 02-menu --cycles 134000000
```

Inspect the checkpoint images before the next action. Only when the menu is
visible, tap Daily Training. Inspect after each subsequent wait; stop as soon
as the helper reports a marker. Do not run a subsequent progression command
merely because it appears in this example:

```powershell
python tools/task_a/route_marker.py --out $out --label 03-select --tap 144 96 --cycles 67000000
python tools/task_a/route_marker.py --out $out --label 04-entry --cycles 67000000
python tools/task_a/route_marker.py --out $out --label 05-marker --cycles 134000000
python tools/task_a/route_marker.py --out $out --label 06-stop --cycles 0 --stop
python tools/task_a/analyze_trace.py $out
python tools/task_a/analyze_marker_route.py $out --before 02-menu
```

Actual run used the checkpoint labels in the table, including the two
helper-only recoveries described above. No RTC override was introduced.
All command execution used explicit approved outside-sandbox requests.

Safety: save semantics changed **no**; Brain Age patched **no**; generated
recomp C manually edited **no**; caller tracing begun **no**; profile-specific
experiment begun **no**; Task B/C begun **no**. No static cross-reference
analysis was necessary. There is no blocker to this route reconciliation;
the optional savestate-export limitation was not needed for the result.
