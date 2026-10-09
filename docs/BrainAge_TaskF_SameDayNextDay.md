# Brain Age Task F: same-day return versus exactly +1 calendar day

Date: 2026-10-09. **Controlled guest dates work; Brain Age distinguishes the
days; both profile returns persist one date-dependent 48-byte record. No
rollover-exclusive save operation was observed. No exercise was started.**

## Baseline and recovery

Used the existing `dev` checkout and `codex/brainage`, starting at Task E
`56a07e4670518d3bf72b67ce38c2109033e649c0`. Public ndsrecomp remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`, with the existing Task A/B/C
observers. ROM SHA-1 is verified by each fresh launch:
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

Authoritative source: `local/task-e/aaa-001/02-quiet-settle/after.sav`, full
262144-byte SHA-256 **H0**:
`fa9c6b3253574bac7d2969943ff29175022264e6cb1e190a2b963e1cd499c40a`.
Profile AAA, birthday 1985-01-01, Brain Age 35. Both runs start from separate
fresh copies of this exact file. Neither uses the other run's changed save.
Both are fresh boots, not restored gameplay states. Task E evidence is
preserved unchanged.

## RTC discovery, control and validation

The existing `rtc_state` debug command reports the actual RTC hardware
registers, not the host date. The existing `--rtc-host` option is unsuitable
for this deterministic comparison and was **not used**. No existing fixed
offset/set-time diagnostic was found.

Before adding the diagnostic, a zero-guest-execution probe recorded the
unmodified RTC default, then imported the preserved Task E completion
checkpoint **only to read its stored RTC**. The probe was terminated without
running guest instructions or providing input. It is not a third gameplay
run. Task E's retained RTC is **2024-01-01 12:03:30**, confirming the creation
calendar day independently of save-field interpretation.

Normal power-on RTC is **2024-01-01 Monday 12:00:00**, raw registers
`[0x24,0x01,0x01,0x01,0x52,0x00,0x00]`, status1 `0x02` (24-hour mode).
Hour decoding masks the PM flag before BCD conversion. The host's October
2026 date is irrelevant. A normal deterministic reboot resets time-of-day;
the same-day claim concerns the retained **calendar day**, not monotonically
advancing real-world time. No negative offset/backward-calendar test was run.

Narrow diagnostic: **`NDS_TASK_F_RTC_PLUS_ONE_DAY=1`**, read once during
`nds_io_reset`, immediately after normal RTC initialization. It invokes the
existing `rtc_count_day()` exactly once, advancing date and weekday while
preserving hour/minute/second, subsecond counters, alarms and status. It does
not advance guest CPU execution or modify cartridge bytes. Unset/non-`1`
values do nothing. No general date-setting interface was added.

Only local framework file `local/ndsrecomp/runner/src/io.cpp` changed: explicit
`<cstdlib>` include and three diagnostic lines. Reproducible ROM-free patch:
`tools/task_f/rtc-plus-one-day.patch`. It is removable with `git apply -R`;
reverse-check passes. The existing runner target rebuilt successfully, with
the baseline's existing warnings left untouched. No generated C was edited.

`tools/task_f/launch_return.py` clears inherited diagnostic values, enables
the switch only for Run B, rejects `--rtc-host`, verifies the authoritative
save hash, and checks the actual RTC **before any guest instruction**.

| Observation | Run A / disabled | Run B / +1 day |
| --- | --- | --- |
| Initial | 2024-01-01 Mon 12:00:00 | 2024-01-02 Tue 12:00:00 |
| After passive startup | 2024-01-01 12:00:10 | 2024-01-02 12:00:10 |
| After Daily Training menu entry | 2024-01-01 12:00:15 | 2024-01-02 12:00:15 |
| After AAA selection settles | 2024-01-01 12:00:19 | 2024-01-02 12:00:19 |
| Final no-input quiet checkpoint | 2024-01-01 12:00:22 | 2024-01-02 12:00:22 |

At every captured before/after RTC sample, the two decoded clocks are
**exactly 86400 seconds / one calendar day apart**, with matching
time-of-day and weekday +1. Run A's complete initial RTC debug state equals
the pre-patch default. Its full CPU/IO state and Flash results after startup
and profile-menu entry match the preserved pre-patch Task E observations
exactly. Disabled behavior is unchanged for these tested boundaries.

The override affects only guest RTC initialization. The ROM, starting save,
host clock, firmware/configuration and RTC ticking semantics were not
changed. No host OS clock API or `--rtc-host` was used.

## Separately measured normal progression

Each phase captures before/after full Flash, RTC, CPU timing, frames,
logical/physical traces and old-byte replay. Both inputs are normal touch:
Daily Training `(144,96)` once, then existing AAA `(195,80)` once.
No More, date edit, confirmation, profile recreation or exercise input.

| Phase | Action and visible result | Requested ARM9 cycles | API operations / submits / accepted bytes / changed bytes, each run |
| --- | --- | ---: | --- |
| 00-initial | Fresh exact H0 load, no guest execution | 0 | 0 / 0 / 0 / 0 |
| 01-passive-startup | No input; title/menu reached | 730000000 | 0 / 0 / 0 / 0 |
| 02-daily-training-entry | Daily Training tap; AAA / Brain Age 35 and three New Data File buttons | 300000000 | 0 / 0 / 0 / 0 |
| 03-select-AAA | AAA tap; automatic profile-entry work; stable selected-profile greeting | 300000000 | **1 / 1 / 48 / 13** |
| 04-quiet-settle | Wait only; same greeting, no additional input | 200000000 | 0 / 0 / 0 / 0 |

The first return write occurs during automatic entry caused by selecting
AAA, **not** during boot or merely entering the profile-selection screen.
Its enclosing operation completes in both runs. No companion operation or
mirror write follows during the captured quiet interval. Normal progression
stops at this first write's stable resulting greeting; no attempt is made to
click through to exercises, the complete home menu or stamp calendar.

### Same-day result

Stable left-screen greeting: **"Happy birthday! Today, you're 39 years old!"**
Right screen: Back and More, More enabled. This is chronological age, not
Brain Age 35. The earlier selection screen still showed AAA / Brain Age 35.

H0 -> **HA**:
`f1edca71c3d5e4fab098869009f32ba81c105f3e40cd5acba6e8b6d8ddd14baa`.
One 48-byte commit operation, 13 changed bytes. Final system cycle
765508318; last commit 535545833; **229962485 system cycles with no further
save activity**. Final Flash snapshot and ordinary disk save both equal HA.

### +1-day result

Stable left-screen greeting: **"Hello!"**, without the birthday greeting.
Right screen: Back and More, More enabled. AAA / Brain Age 35 was recognized
before selection. No date-confirmation prompt appeared at this boundary.

H0 -> **HB**:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
One 48-byte commit operation, 13 changed bytes. Final system cycle
765197312; last commit 535545833; **229651479 system cycles without further
save activity**. Final Flash snapshot and ordinary disk save both equal HB.

## Complete first-return request and causal attribution

Both runs use ARM9 callsite **`0x0202D744`**, return **`0x0202D748`**, API
**`0x0200DE78`**, source **`0x020E95FC`**. Target **`0x7040`**, length
**48 bytes**, one transport submission through staging **`0x020D4F60`** and
shared request **`0x020D4CE0`**. FIFO word **`0x1EB`**. No new caller graph.

| Local event / PC | System cycle, both runs | Run A ARM9 instruction | Run B ARM9 instruction |
| --- | ---: | ---: | ---: |
| 1 API `0x0200DE78` | 535537703 | 110440679 | 110440697 |
| 2 submit `0x0200E080` | 535537899 | 110440838 | 110440856 |
| 3 send `0x020091B0` | 535537985 | 110440914 | 110440932 |
| 4 ARM7 receive `0x037FE230` | 535538115 | ARM7 37695326 | Same |
| 5 ARM7 worker `0x03802F48` | 535538680 | ARM7 37695596 | Same |

Payload is identical across each run's API, submit, FIFO send/receive and
worker; committed bytes match it exactly. One writing Flash transaction
**259**, command **`0x0A`**, sequences **1..48**, offsets **`0x7040..0x706F`**,
SPI positions **4..51**, final event `last=true`.

Every carried command/byte origin is **ARM7 `0x038032B8`**, ARM mode, Tier-3;
host commit path **`flash_spi_write`**. Command-origin system cycle
535539667, instruction 37696099. First byte cycle 535540192, instruction
37696363, `0x7040: 00 -> 02`. Last byte cycle 535545833, instruction
37699136, `0x706F: 00 -> FE`. Both traces retain causal origin snapshots;
no incidental PC sampling at the host commit was introduced.

## Byte diff and controlled date dependence

Full written span is 48 bytes; **13 values change**, **35 accepted bytes are
unchanged**. Both baselines have zero at the changed offsets. Exact changed
ranges, inclusive, in both runs:

`0x7040`, `0x7044`, `0x7047`, `0x705A`, `0x7060..0x7066`,
`0x706E..0x706F`.

| Offset | Before | Run A after | Run B after |
| --- | --- | --- | --- |
| `0x7040` | `00` | `02` | `02` |
| `0x7044` | `00` | `01` | `01` |
| `0x7047` | `00` | `02` | `02` |
| `0x705A` | `00` | `FF` | `FF` |
| `0x7060..0x7066` | `00000000000000` | `23180101180101` | `23180101180102` |
| `0x706E..0x706F` | `0000` | `A4FE` | `A3FE` |

The **entire two final saves differ at exactly two bytes**:
`0x7066: 01 -> 02` and `0x706E: A4 -> A3`. All other bytes, including the
profile/signature structures and Brain Age result, are identical. Independent
replay checks all 48 old bytes and reproduces each complete live image.
These fresh runs retain ordinary automatic disk write-through: their disk
files equal the final snapshots without manual export/reload intervention.

## Comparison and conclusion

- **PROVEN:** guest-visible clocks differ by exactly +1 calendar day;
  profile selection recognizes AAA / Brain Age 35 on both; January 1 shows
  the birthday/39 greeting and January 2 does not; each profile entry commits
  the same 48-byte operation at identical request/commit system times; the
  final saves differ only at the two listed bytes.
- **SUPPORTED:** the return record is date-dependent profile-entry
  bookkeeping. The controlled day difference tracks a stored `01` versus
  `02` byte and a companion byte. The greeting also independently demonstrates
  that game logic consumes the changed calendar date.
- **INFERENCE/unmapped:** formal record layout, companion-byte checksum
  meaning, journal/index semantics, full home/calendar/stamp state and later
  day-specific behavior. No signature algorithm or full date/save map.

**Guest RTC/day control works: yes, for this +1-day fresh-return experiment.**
**Brain Age recognizes the next calendar day: yes at the observed profile
entry/greeting boundary.** Continuous execution across midnight is not tested.

**Day rollover alone triggers a standalone persistent operation: no such
operation is established.** RTC advance/passive boot/profile-menu entry
produce zero writes. Selecting AAA does persist a date-dependent record on
the next day **without an exercise**, but the same-day control also does so.
Thus it is incorrect either to claim a rollover-exclusive write or to claim
that the +1-day profile return made no write. This distinction is the main
result. No exercise started; no Task G.

## Changes, validation and artifacts

ROM-free project files:

- `tools/task_f/rtc-plus-one-day.patch`: opt-in local runtime diagnostic.
- `tools/task_f/launch_return.py`: authoritative-save gate, isolated child
  environment, before-execution RTC validation and host-time rejection.
- `tools/task_f/analyze_return.py`: reuses Task E's complete source/page/Flash
  auditor; asserts exact clock differential at every phase, initial save
  identity, only one completed operation, final two-byte diff, disk identity
  and disabled behavior against pre-patch Task E states.
- `tools/task_e/capture.py`: read-only before/after RTC capture and an explicit
  1..3 tap limit. Default remains one for Task E; Task F authorizes at most
  three and actually performs only two per run. No stop guard in Task D was
  modified.
- This document.

Validation: existing runner build, patch reverse-check, Python compilation,
complete request/Flash replay, exact-date comparator, legacy-disabled state
comparison, automatic disk-image identity and `git diff --check` pass. A
reproduction-patch context typo was corrected before either run; it did not
affect the actual diagnostic or runtime results. Existing build warnings
were not silenced. No broader validation/performance matrix.

Normal sandbox setup still fails before execution with
`helper_unknown_error: setup refresh had errors`. Supported individually
requested `require_escalated` execution worked under auto-review without
Graham approval spam, human escalation or approval-capacity failure. No
approval settings/infrastructure or host clock was changed.

All screenshots, saves, states, generated artifacts and raw captures stay
ignored locally. Only ROM-free source/patch/documentation is committed.
Local paths:

- `local/task-f/source-rtc-check/rtc-evidence.json`: pre-patch default and
  retained Task E RTC; zero-guest-execution artifact probe.
- `local/task-f/rtc-build.log`: existing runner target rebuild.
- `local/task-f/same-day-001/` and `next-day-001/`: independent original-save
  copies, isolated launches, RTC control metadata, all phase snapshots,
  before/after images, debug logs, causal traces and checkpoints.
- Each run's `04-quiet-settle/after.sav`: exact final snapshot.
- `local/task-f/return-audit.json`: complete causal/RTC/disk comparison.

Representative continuation commands, using the supported approval path:

```powershell
git -C local/ndsrecomp apply --check ../../tools/task_f/rtc-plus-one-day.patch
git -C local/ndsrecomp apply ../../tools/task_f/rtc-plus-one-day.patch
cmake --build build/task-a-runner --target nds_runner --parallel 2
python tools/task_f/launch_return.py --source local/task-e/aaa-001/02-quiet-settle --out local/task-f/same-day-001 --port 19855
python tools/task_f/launch_return.py --source local/task-e/aaa-001/02-quiet-settle --out local/task-f/next-day-001 --port 19856 --plus-one-day
python tools/task_e/capture.py --out local/task-f/same-day-001 --label 00-initial --cycles 0 --max-taps 3
python tools/task_e/capture.py --out local/task-f/same-day-001 --label 01-passive-startup --cycles 730000000 --max-taps 3 --savestate
python tools/task_e/capture.py --out local/task-f/same-day-001 --label 02-daily-training-entry --tap 144 96 --cycles 300000000 --max-taps 3 --savestate
python tools/task_e/capture.py --out local/task-f/same-day-001 --label 03-select-AAA --tap 195 80 --cycles 300000000 --max-taps 3 --savestate
python tools/task_e/capture.py --out local/task-f/same-day-001 --label 04-quiet-settle --cycles 200000000 --max-taps 3 --savestate
python tools/task_f/analyze_return.py --same local/task-f/same-day-001 --next local/task-f/next-day-001 --output local/task-f/return-audit.json
```

The next-day run uses the identical phase commands with its own directory;
no input beyond those two taps. Check whether the patch is already installed
with reverse-check before applying it; do not overwrite old evidence
directories. Use the existing local GCC/w64devkit build environment. The
RTC reference is the preserved artifact probe; a new workspace must capture
its default and retained Task E `rtc_state` similarly before executing the
controls. Both tested runners and the probe are terminated; none remains.

**STOP AFTER TASK F. Do not begin Task G.**
