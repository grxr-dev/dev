# Brain Age Task D: first profile-creation persistent write

Date: 2026-10-09. Result: **first write identified; signature-dependent data proven by one controlled replay**.

## Recovery and scope

Used the existing `dev` checkout on `codex/brainage`, starting at Task C
commit `fe0469152116882ee55319b1cd35dc874ba30815`. Public ndsrecomp remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`; the existing instrumented
`build/task-a-runner/nds_runner.exe` was reused without rebuilding it.
Task A/B/C tracing and `config/brainage_task_a.toml` are unchanged.
ROM SHA-1 was checked by each restore/reload helper and matches
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

Restored `local/task-c/recovered-003/37-measured-result-settle/checkpoint.state`
into a new `local/task-d/route-001/` directory. Source state SHA-256:
`2538e96b8043338f4dfdf9e4c525694f25a187d96f66f08b4e197976eede5e9b`.
CPU control state, cycles and instruction counts matched the source exactly.
The visible state was the completed Calculations Brain Age Check's pre-name
introduction: "You know, I never even asked you your name! How negligent of
me!" More enabled, not pressed. Restored ARM9 cycles: 11138996880;
ARM7/system cycles: 5569498440. Full 262144-byte Flash matched the source;
`CLEAR-RAM-CHECK` remained at `0x180`. All Task C evidence is untouched.

Hash abbreviations used in the transition table:

- **H0**: `f8310763e5c388ceeb82b520c20fcd88e35a3c93af14db7d3dcaebcec292ede0`.
- **H1**: `3fdf2a3ae7feea6a89c99fc6b858c541ef62d75af67c6565c01ec4b8f9a01b6c`.
- **HB**: `1abd78347e8aecc28499e1d77ec441864607061d60f5a49f65cdc1693589013b`.

## Separately measured transitions

Each checkpoint captures before/after full Flash, images, CPU timing,
logical/physical traces, and a byte-exact replay check. Normal touch for
More/Select is raw `(240,152)`; touches are released automatically. Ink is
ordinary guest touch input, not a RAM/profile injection. The name is a
**handwritten signature bitmap**, not an ASCII text/name-entry keyboard.

| No. / local label | Starting state; one action | Resulting state | Submit / byte commits / changed bytes | Before -> after | Final ARM9 cycles |
| --- | --- | --- | --- | --- | ---: |
| 00-baseline | Restored pre-name introduction; no input/cycles | Same | 0 / 0 / 0 | H0 -> H0 | 11138996880 |
| 01-pre-name-more | Pre-name introduction; More | "In order to save your brain age file," | 0 / 0 / 0 | H0 -> H0 | 11272996993 |
| 02-save-file-introduction | Save-file introduction; More | "I need you to input a little bit of personal data." | 0 / 0 / 0 | H0 -> H0 | 11406997504 |
| 03-personal-data-introduction | Personal-data introduction; More | Sign-name canvas, Select disabled | 0 / 0 / 0 | H0 -> H0 | 11541202402 |
| 04-enter-AAA | Empty signature canvas; draw AAA | AAA visible on canvas and preview; Select enabled | 0 / 0 / 0 | H0 -> H0 | 11675202464 |
| 05-select-AAA | Visible AAA; Select | Automatic age introduction begins; no separate name-confirm question | 0 / 0 / 0 | H0 -> H0 | 11809386108 |
| 05b-select-settle | Same automatic transition; wait only | "Oh, yes! I need to ask your age. Terribly sorry about that!" More enabled | 0 / 0 / 0 | H0 -> H0 | 12009795584 |
| 06-age-introduction | Age introduction; More | Last-two-birth-year-digit canvas, prefix 19 | 0 / 0 / 0 | H0 -> H0 | 12210266508 |
| 07-enter-birth-year-1985 | Empty year canvas; write 85 | Visible 1985; Select enabled | 0 / 0 / 0 | H0 -> H0 | 12410791692 |
| 08-select-birth-year | Visible 1985; Select | Birth-month canvas | 0 / 0 / 0 | H0 -> H0 | 12611389200 |
| 09-enter-birth-month-01 | Empty month canvas; write 01 | Visible 01; Select enabled | 0 / 0 / 0 | H0 -> H0 | 12811389320 |
| 10-select-birth-month | Visible 01 month; Select | Birth-day canvas | 0 / 0 / 0 | H0 -> H0 | 13011389328 |
| 11-enter-birth-day-01 | Empty day canvas; write 01 | Visible 01; Select enabled | 0 / 0 / 0 | H0 -> H0 | 13212031452 |
| 12-select-birth-day | Visible 01 day; Select | Review AAA and birthday 1985-01-01; More enabled | 0 / 0 / 0 | H0 -> H0 | 13412032130 |
| 13-confirm-profile-review | Review; More | "Touch Select if it's OK or Revise if it's not." Select/Revise enabled | 0 / 0 / 0 | H0 -> H0 | 13612032288 |
| **14-select-profile-details** | **AAA / 1985-01-01 review; Select** | **First write captured while the same review screen remains visible** | **1 / 256 / 245** | **H0 -> H1** | **13613772800** |

All pre-target logical trace files are empty, not just zero net Flash diffs.
The original generic initialization had 193 submits and 33200 Flash byte
commits. Restored sessions reset diagnostic sequence numbers; their zero
baseline does not mean those historical initialization events did not occur.

The first event is not signature drawing, selecting the name alone, birth
field entry, or the More instruction on the review screen. It is the actual
**Select confirmation of the reviewed profile details**. No later profile
screen was clicked. Monitoring consumed traces after 100000-ARM9-cycle
execution batches, with the existing bounded scheduler-resume handling. It
stopped at the first batch containing the request; that batch already
contained its completed first page. "Immediately" means this measured batch
resolution, not a new emulator instruction-break facility.

Savestates succeeded at all main checkpoints except 09, where the existing
export returned `savestate GPU3D command state is invalid`. Flash/screenshots
and traces remain valid. Successful pre-confirmation states exist at 04,
07, 11 and especially 13. No emulator workaround was applied.

## First request and causal transport

The new immediate ARM9 caller is **callsite `0x0202E8E8`**, returning to
`0x0202E8EC`, rather than the earlier marker owner `0x0202FCC0`. The bounded
static check verifies `BL 0x0200DE78` there and `mov r2,#0x700` immediately
before it. No symbol name or larger caller graph is claimed.

The first high-level write API asks for **1792 bytes (`0x700`) at `0x600`**,
original payload **`0x020E8E94`**. Its captured full payload is local only.
The transport stages the first **256-byte** page at **`0x020D4F60`**, using
shared request **`0x020D4CE0`** and the established +0x0C/+0x10/+0x14 fields.

| Local event | Core / boundary PC | Offset / length / payload | System cycle | Instruction ordinal |
| --- | --- | --- | ---: | ---: |
| 1 write_api | ARM9 `0x0200DE78`, LR `0x0202E8EC` | `0x600` / 1792 / `0x020E8E94` | 6806828215 | 1014041263 |
| 2 submit | ARM9 `0x0200E080` | `0x600` / 256 / `0x020D4F60` | 6806828733 | 1014041660 |
| 3 fifo_send | ARM9 `0x020091B0` | Same first page; FIFO `0x1EB` | 6806828819 | 1014041736 |
| 4 fifo_receive | ARM7 `0x037FE230` | Same shared fields, payload and FIFO word | 6806828992 | 421880584 |
| 5 arm7_write | ARM7 `0x03802F48` | Same first page | 6806829557 | 421880854 |

All events use ARM mode / Tier-3. Payload identity is verified from the
write API's first 256 bytes through submit, send, receive and worker to the
final live Flash page; this is not merely a temporal association.

**Important boundary:** only the first transport page was allowed to commit.
The enclosing 1792-byte API operation has **1536 further requested bytes**
not observed as commits here. It was deliberately not drained to a completed
profile, and no mirror write or profile-created flag is established. The
first transport submission is complete; the full creation/save is not.

## Flash result

One writing SPI transaction, local ID **5**, command **`0x0A`**, commits
**256 individual bytes** at `0x600..0x6FF`; 245 change from their erased `FF`
values and 11 accepted bytes remain `FF`. Nothing else changes. Independent
old-byte replay reproduces the full 256 KiB live image exactly.

Contiguous changed ranges, inclusive:

`0x600..0x613`, `0x615..0x616`, `0x618..0x653`, `0x655..0x66A`,
`0x66C..0x684`, `0x686..0x690`, `0x692..0x697`, `0x699..0x6A4`,
`0x6A6..0x6D3`, `0x6D5..0x6DF`, `0x6E1..0x6EC`, `0x6EE..0x6FF`.

Focused before/after hex (all before bytes here are `FF`):

| Offset / length | New bytes |
| --- | --- |
| `0x600` / 20 | `59617a300000180000000000000000008f000000` |
| `0x615` / 2 | `0111` |
| `0x692` / 6 | `05a10e15f906` |
| `0x6D5` / 11 | `0646fd1818c6fd0e07d8e6` |
| `0x6E1` / 12 | `5f16b28046fd3e0f06fdcc7e` |
| `0x6EE` / 18 | `d8560e347df70d07ccc0f050ee0146fd03f8` |

Every commit's carried command and byte origins are **ARM7 `0x038032B8`**,
ARM mode, Tier-3, with commit path `flash_spi_write`. No final-helper PC
sampling was introduced. Representative exact event fields:

| Field | First byte | Last byte |
| --- | --- | --- |
| sequence / transaction / command | 1 / 5 / `0x0A` | 256 / 5 / `0x0A` |
| offset / old -> new | `0x600`, `FF -> 59` | `0x6FF`, `FF -> F8` |
| SPI position / last | 4 / false | 259 / true |
| command-origin cycle / instruction | 6806830544 / 421881357 | Same carried origin |
| byte-origin cycle / instruction | 6806831069 / 421881621 | 6806861670 / 421896666 |

Per-byte full events and full before/after range hex are preserved locally,
not committed as raw game-derived captures.

## One controlled signature differential and classification

Restored the existing empty-signature checkpoint 03 into
`local/task-d/differential-001/`. Replayed the same normal route with **BBB
instead of AAA**, keeping birthday 1985-01-01, prior handedness, Calculations
result and requested input/wait budgets unchanged. No other profile value
was changed. Both signatures were visually verified on the final review.
Both pre-confirmation Flash images were exactly H0. From the birth-year
entry checkpoint onward even the ARM9/ARM7 cycle endpoints matched exactly;
all five final request boundary **system-cycle timestamps are identical**.
Instruction ordinals differ, as expected for different drawn strokes.

The controlled run produces the same high-level callsite, offset, 1792-byte
API length, source pointer, 256-byte staging pointer, shared request and FIFO
correlation. Both stop on their first page. Of the 1792 source-payload bytes,
**275 differ**; of the first 256 staged/committed bytes, **224 differ**.
BBB changes 231 bytes from H0 and results in HB. The common prefix starts
with `59617a30` (ASCII `Yaz0`); the body is encoded, not an ASCII `AAA`/`BBB`
string. No complete save-format or compression decoder was implemented.

Classification: **D, clearly user-specific profile data**, for the tested
first page, not a claim of a completely created/persisted profile.

- **PROVEN DYNAMICALLY:** this is the first observed post-marker write;
  actual profile-details Select triggers it; changing only signature input
  changes the corresponding request payload and committed page at identical
  request timings. It is not input-independent generic initialization.
- **SUPPORTED:** the first write contains an encoded representation derived
  from the user-drawn signature. The UI is a signature canvas, and the
  differential changes that input alone.
- **INFERENCE:** its precise bitmap/compression layout, other profile fields,
  checksums, allocation state and later mirror/commit ordering. These were
  not mapped. No birthday, handedness, score or profile-created byte is
  independently identified in this first page.

## Persistence check and deliberate limitations

Savestate import intentionally detaches ordinary battery write-through in
this framework baseline. Consequently live H1 differs from the restored
session's original H0 `erased.sav`; this is expected, not a new save bug.
The legitimate `cart_save` snapshot was already preserved as `after.sav`.
No persistence flag or Flash semantics was changed.

After preserving both captures, terminated only the two verified Task D
runner PIDs. A clean runner was launched with a copy of the observed H1
snapshot as its ordinary `--save-path`, **without savestate import**.
`cart_save` read back all 262144 bytes exactly, SHA-256 H1; both guest
instruction counts remained zero. That runner was then terminated.

Thus **snapshot export / clean save-file reload is verified**. Automatic
write-through durability from a restored state is **not** claimed. Created
profile recognition after guest boot is **not tested**: the enclosing
1792-byte operation was deliberately interrupted after its first page, and
finishing creation or booting through further save logic would go beyond
this first-write boundary. An incomplete profile is not presented as a
completed persistent profile. No gameplay followed reload.

## Changes, validation and reproduction

ROM-free project changes:

- `tools/task_c/step.py`: optional validated JSON normal-touch strokes,
  recorded in summaries, preserving the existing first-request stop guard.
- `tools/task_d/signature.py`: deterministic AAA/BBB canvas paths and
  birth-field 85/01 paths; uses real pen input.
- `tools/task_d/analyze_first_write.py`: bounded request/page correlation,
  old-byte replay, exact ranges and optional one-input comparison.
- `tools/task_d/reload_snapshot.py`: isolated clean snapshot-file reload
  check with no guest instruction execution; always terminates its runner.
- This document.

No runtime source, Flash semantics, game bytes, generated recomp C, framework
baseline, coverage banks or approval infrastructure was changed. No Task E,
voice-route comparison, RTC/day experiment or exercises were performed.

All actual command operations used supported `require_escalated` requests
under the unchanged auto-review policy. They proceeded without Graham
approval spam or human escalation; no approval-capacity failure occurred.
No full-access or approval-policy override was enabled. The existing
reparse-point patch restriction required the bundled apply_patch helper.

Validation: Python compilation of all changed helpers, independent replay
and request-to-Flash audit for both runs, exact-system-cycle differential
assertions, full-image clean reload and `git diff --check` passed.

Representative commands, from the existing checkout:

```powershell
python tools/task_c/restore.py --source local/task-c/recovered-003/37-measured-result-settle --out local/task-d/route-001 --port 19855
python tools/task_c/step.py --out local/task-d/route-001 --label 00-baseline --baseline --cycles 0 --savestate
python tools/task_d/signature.py AAA local/task-d/route-001/AAA-strokes.json
python tools/task_d/signature.py 85 local/task-d/route-001/85-strokes.json
python tools/task_d/signature.py 01 local/task-d/route-001/01-strokes.json
python tools/task_c/step.py --out local/task-d/route-001 --label 04-enter-AAA --strokes local/task-d/route-001/AAA-strokes.json --cycles 134000000 --savestate
python tools/task_c/step.py --out local/task-d/route-001 --label 14-select-profile-details --tap 240 152 --cycles 200000000 --savestate
python tools/task_d/analyze_first_write.py local/task-d/route-001/14-select-profile-details --differential local/task-d/differential-001/14-select-profile-details --output local/task-d/first-write-audit.json
python tools/task_d/reload_snapshot.py --source local/task-d/route-001/14-select-profile-details --out local/task-d/reload-001
```

The transition commands above illustrate helpers, not permission to skip
the intermediate measured actions in the table. Existing directories must
not be overwritten. Each main label requests 134000000 ARM9 cycles through
05, then 200000000 from 05b onward, but first-request stopping shortens 14.
The differential uses exactly the same budgets and inputs except BBB.

Ignored local evidence:

- `local/task-d/route-001/`: restored baseline, per-transition before/after
  saves/images/states/debug traces, `flash.jsonl`, `requests.jsonl`, session.
- `local/task-d/differential-001/`: one BBB control and its first-write stop.
- `local/task-d/first-write-audit.json`: exact local payloads, ranges, causal
  events, independent replay and differential results.
- `local/task-d/reload-001/`: copied observed snapshot, clean launch logs,
  zero-instruction `reload.json` evidence.

No ROM-derived runtime output is committed or uploaded. Claims apply only
to the tested **Calculations onboarding route**; voice/Stroop equivalence is
not claimed. **Stop after Task D.**
