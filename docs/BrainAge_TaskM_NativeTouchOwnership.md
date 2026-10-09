# Brain Age Task M: DS-coordinate touch ownership in the native mini-exercise

Date: 2026-10-09. **PASS on the normal compiled lifecycle-entry path.**
The authoritative native interaction is six ordinary DS-coordinate taps:
**3 -> premature Continue -> 5 -> premature Continue -> 4 -> Continue**.
All twelve down/up events enter the runner's shared `nds_set_touch` abstraction,
are consumed by the native owner and deliver zero events to the guest.
Both CPUs remain frozen. The final pen-up resumes the untouched transition
once; original rules and Back work, with zero save operations or changed bytes.
This is host-rendered UI, not DS rendering, physical-platform input validation
or handwriting integration.

## Identity, recovery and baseline

Existing `dev`, branch `codex/brainage`, started at Task L
`91b5506871290558e958b90ec9b4c71f75aa3a55`. Framework HEAD remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`, with the preserved local diagnostic
integration. ROM SHA-1 was independently checked and is also verified by the
launcher/runner: `b8a105bacc3234dede8d4465df0869f2b922a0e2`.

Restored the unchanged Task G source
`local/task-g/session-001/04-training-menu/checkpoint.state`, SHA-256
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
AAA, January 2, 2024, 12:00:34 guest RTC, ordinary Training selection menu.
Full starting/final Flash SHA-256, **H0**:

`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Task K's readable `local/task-k/normal-disabled-001/` reference was reused;
the copied integrity manifest is checked by the final audit. No old evidence
was modified. Launch omits `--force-tier3`; restoration disables the saved
inherited force selector before guest execution. Its inherited miss count
113582860 stays unchanged. The target callback explicitly reports compiled
execution, not a forced fallback. Rules initialization naturally remains Tier-3
in the established bank inventory, which does not alter the compiled entry proof.

## Existing ordinary touch path and threading

`runner/src/debug_server.cpp` handles `touch {x,y,down}` by calling
`nds_set_touch(uint16_t x,uint16_t y,bool down)` in `io.cpp`.
`frontend.cpp` also uses that setter for scripted pen events, normalized mouse
coordinates and pen motion/release. Coordinates represent DS pixels in
0..255 x 0..191. Repeated down updates are motion; false is pen release.
The existing setter converts down coordinates to ADC values with `x << 4`
and `y << 4` and clears EXTKEYIN's pen-up bit. Release sets ADC X=0,
ADC Y=0xFFF and sets the pen-up bit. That is the guest delivery point.

The headless debug handler executes `run_cycles` synchronously. It cannot
serve another regular touch request while buried inside the native hold.
The frontend debug pump likewise hands mutations to its owning emulation/
frontend thread. Neither the existing setter nor the new owner API is a
cross-thread guest-mutation facility.

The small solution is an additional **generic raw-touch adapter** in the
existing runner-owned host control channel, polled by the panel's Win32 timer
on that same held emulation thread. It invokes the very same `nds_set_touch`
used by the normal TCP command and frontend, rather than invoking a choice
handler directly. No receiver thread, guest queue, extra server, scheduler
tick, unfreeze or answer-specific hidden shortcut is required. This adapter
proves the shared runner abstraction, not real SDL/physical input handling
while the host panel is active on every platform.

## Narrow implementation and ownership

ROM-free sources/support:

- `tools/task_m/touch-owner.patch`: optional `NdsTouchOwner` callback/context
  before guest mutation, plus read-only ADC/contact/owner/delivery observations.
- `tools/task_m/touch-debug.patch`: read-only `touch_state` debug command.
- `tools/task_m/touch_state.h`: hit regions and host-only contact edge tracking.
- `tools/task_j/brainage_native_probe.h`: shared owner scope, generic touch
  adapter, routing to the existing validator, contact/audit fields and layout.
- `tools/task_k/install.py`: idempotent installation of owned headers and the
  two small runtime patches. `launch.py`, J `context.py` and J `control.py`
  permit isolated Task M roots; context adds read-only contact inspection.
- `tools/task_m/drive.py`: sequenced raw down/up sender with read-only samples.
- `tools/task_m/state_test.cpp`, `analyze.py`: contact tests and compact audit.

Local installed runtime changes are confined to
`local/ndsrecomp/runner/src/{io.h,io.cpp,debug_server.cpp,brainage_native_probe.h,touch_state.h}`.
The existing MiniExercise header and guest hook mechanisms are unchanged.
Only the runner was rebuilt; no generated bank regeneration or manual edit.

Activation is unchanged: `NDS_TASK_J_CUSTOM_EXERCISE_PROBE=1`, disabled by
default and gated on the exact ROM and original lifecycle context. The owner
is installed only inside the active native panel. A scoped cleanup removes it
even if the panel throws. Installation requires already released/clean guest
contact; it does not forge input RAM or change an existing guest contact.

When owned, **all** touch events are consumed before ADC/key mutation.
Outside-region contacts are ignored; motion out of the pressed target cancels
that contact's action. A down begins a contact, repeated down is motion, and
only its up resolves a choice/Continue. Up coordinates need not be meaningful,
matching the ordinary guest setter's release convention. Duplicate up cannot
generate a second action. Choices and Continue use the same host-only quiz
validator from L. Continue before completion is rejected. Final Continue
resolves on up, so there is no deferred pen-up to leak after owner removal.
No input is queued for later replay.

Before removal, the runtime verifies native contact is released, guest ADCs
are still 0/0xFFF, guest pen is up and its delivery counter has not changed.
Only then is ownership removed and original execution resumed naturally.
The inactive setter executes its original body unchanged; its added delivery
counter is host diagnostic state, not a guest register or serialized save value.
The owner API must be used on the existing owning thread.

## Layout and session-safe raw controls

Inclusive DS hit regions and authoritative centers:

| Target | X | Y | Center |
| --- | --- | --- | --- |
| 3 | 24..84 | 96..136 | (54,116) |
| 4 | 98..158 | 96..136 | (128,116) |
| 5 | 172..232 | 96..136 | (202,116) |
| Continue | 72..184 | 148..184 | (128,166) |

Native controls use corresponding 2x DS-pixel positions/sizes. Captured actual
host client is 512x393; no DS framebuffer is written by the custom state.
Initial, both incorrect states and correct/completed state were visually
inspected. Continue is disabled until correct, and choices disable afterwards.

Existing file protocol now also accepts:

```text
SESSION SEQUENCE touch X Y DOWN
SESSION SEQUENCE sample
```

DOWN is 0 or 1. Bounds and field count are validated. Every event/sample
requires the exact fresh panel session and next positive command sequence,
using L's ControlOrder. Atomic file publication, unchanged-file suppression,
token checks and sequence checks prevent stale/replayed controls. All mutable
quiz state remains host-only. Legacy L choose/continue commands remain for
earlier reproductions but are **not used** in the Task M authoritative run.

## Authoritative interaction and freeze

Root: `local/task-m/normal-enabled-001/`, port 19871. Runner PID 170844 was
identity-verified and stopped after capture/audit, while paused at Training.

The normal menu tap is (166,75). The exact compiled gate is unchanged:

```text
ARM9 ARM; PC 0204D790; opcode E92D4030; LR 02050268; R0=41
current 020DA464=32; requested 020DA3EC=41
selected 020DA3F0=11; Training context 020DA420=1
```

| Commands | Raw tap/sample | Result |
| --- | --- | --- |
| 1 | initial sample | 0 attempts; question; held |
| 2/3, 4 | down/up (54,116), sample | attempt 1, answer 3, incorrect |
| 5/6, 7 | down/up (128,166), sample | Continue rejected; still attempt 1 |
| 8/9, 10 | down/up (202,116), sample | attempt 2, answer 5, incorrect |
| 11/12, 13 | down/up (128,166), sample | Continue rejected; still attempt 2 |
| 14/15, 16 | down/up (128,116), sample | attempt 3, answer 4, completed |
| 17 | post-completion held sample | completed; guest still held |
| 18/19 | down/up (128,166) | one accepted Continue, on up |

Seven diagnostic commands are **sample only**. Twelve touch events are sourced
`ds_touch`, owned/consumed=true, per-event guest deliveries=0. Choice/Continue
events are derived inside the owner callback, not answer-specific commands.
Runtime events 12 and 21 reject premature Continue; event 31 accepts the final
Continue; 32 verifies clean release, 33 removes the owner, 34 resumes original.
No `native_ui` action occurred. Native captures are
`native-panel.bmp.{3,8,17,26}.bmp` and stay local.

All 34 runtime rows preserve identical registers/CPSR snapshot, Flash digest,
nonterminal guest state and these exact counters:

| Field | Frozen value |
| --- | --- |
| current/requested/selected | 0x32 / 0x41 / 0x11 |
| ARM9 cycles | 2320143205 |
| ARM7 scheduler cycles | 1160071557 |
| ARM9 / ARM7 ordinals | 209008089 / 69059507 |
| guest ADC X/Y; pen | 0 / 4095; released |
| guest touch delivery count | 2 (the original menu down/up only) |
| Flash SHA-1 | a8a960103e51212efdc5bdcb5cbc28d862deb860 |

Initial through post-completion sampling lasts at least six host seconds.
Only the lifecycle entry has been observed before final Continue: rules init
has not run, both save traces are empty, and no guest cycles/events advance.
The callback preserves original compiled stack/LR context and returns once;
no guest scene/register values are forged.

## Resume, no-leak settle, Back and inactive behavior

First stable rules context, both CPU/I/O/dispatch views, rules object bytes,
both original screen images and full Flash match Task K's disabled reference
**exactly** after excluding the added read-only touch-observation field.
Current=requested=0x41, selected=0x11, menu context=1, rules object
0x020E9A00, calculation object=null. One rules initializer, no calculation
constructor, no duplicate entry or invalid CPU/dispatch state.

A no-input settling budget of 30000000 ARM9 cycles was then applied. Rules
scene/globals remain unchanged; guest pen stays released, owner=false and
guest delivery count stays exactly 2. Touch-screen rules image B is byte-identical.
Screen A's normal animated portrait changes; that expected animation was
visually checked rather than requiring full-frame identity across advancing
guest time. There is no More/Back/Start or other input-induced transition.

Original Back is then tapped once at (240,32), settling 150000000 cycles.
Current=requested=0x32, selected=0x11, menu context=1; Training restored and
calculation object remains null. Guest delivery count is now 4: exactly the
normal Back down/up, with clean contact and no owner. This plus code inspection
proves ordinary inactive delivery is unchanged. No original Start or problem
answer, original completion, custom save/result write or progression credit.

All four phase captures show **0 logical save requests, 0 Flash commits,
0 accepted bytes and 0 changed bytes**, full SHA-256 H0 throughout. Independent
old-byte replay matches live and disk snapshots. Lifecycle entries are only
the original rules transition and normal Back; rules init=1, constructor=0.

## Reproduction and artifacts

From `dev`, with the prepared pinned framework/build and unchanged source state:

```powershell
python tools/task_k/install.py --codex-executable <bundled-codex.exe>
g++ -std=c++17 -Wall -Wextra -I tools/task_m tools/task_m/state_test.cpp -o local/task-m/state_test.exe
local/task-m/state_test.exe
cmake --build build/task-a-runner --target nds_runner --parallel 2
python tools/task_k/launch.py --out local/task-m/<fresh-run> --port 19871 --enabled
python tools/task_g/capture.py --out local/task-m/<fresh-run> --label 00-menu --cycles 0
python tools/task_j/context.py --out local/task-m/<fresh-run> --name menu
```

Run selection capture and the raw-touch driver concurrently: selection remains
blocked until the driver supplies the deliberate final Continue.

```powershell
python tools/task_g/capture.py --out local/task-m/<fresh-run> --label 01-select-x20 --tap 166 75 --cycles 150000000
python tools/task_m/drive.py --out local/task-m/<fresh-run>
```

After selection capture finishes:

```powershell
python tools/task_j/context.py --out local/task-m/<fresh-run> --name rules
python tools/task_g/capture.py --out local/task-m/<fresh-run> --label 02-rules-no-input --cycles 30000000
python tools/task_j/context.py --out local/task-m/<fresh-run> --name rules-settled
python tools/task_g/capture.py --out local/task-m/<fresh-run> --label 03-normal-back --tap 240 32 --cycles 150000000
python tools/task_j/context.py --out local/task-m/<fresh-run> --name returned-menu
python tools/task_m/analyze.py --out local/task-m/<fresh-run>
```

The analyzer requires the preserved `local/task-m/reference-integrity.json`,
copied from L's manifest of unchanged K reference/source hashes. Actual build
logs: `local/task-m/build.log`, `build-final.log`; executable:
`build/task-a-runner/nds_runner.exe`. Contact unit tests, Python compilation,
installation idempotence and Git whitespace checks pass. Existing framework
warnings (extern definitions, misleading indentation, unused functions and
an old missing initializer) were not modified; none originates in the added
touch/header code. No broad gameplay/benchmark matrix or forced-path rerun.

Compact runtime evidence: `native-probe.jsonl`, `touch-inputs.json`,
`interaction-proof.json`, `entries.jsonl`, context JSONs and **`audit.json`**
(34 runtime + 3 derived events). Phase snapshots/logs/images are under
`00-menu/`, `01-select-x20/`, `02-rules-no-input/`, `03-normal-back/`.
Everything ROM/save/image-derived remains ignored under `local/`; only the
ROM-free sources, patches and this report are committed.

## Execution posture, limits and next experiment

The first normal sandbox read failed before execution with
`Failed to create unified exec process: helper_unknown_error: setup refresh had errors`.
Subsequent narrowly justified supported escalated operations worked under
auto-review; no human approval was required, policy/full-access/relay changes
were not made. This is an actual environment issue, not a gameplay blocker.

**Proven:** runner DS-coordinate events can be exclusively owned by the native
exercise, processed interactively while both guest CPUs are frozen, consumed
without guest delivery, and released cleanly before original compiled flow.
Normal rules/Back and unchanged saves are preserved.

**Not proven:** DS-rendered custom UI, physical frontend/platform integration,
Decuma/stylus handwriting, guest score/history/save integration, custom menu
entries or voice integration. Task M stops here.

Recommended Task N only: render the same tiny panel through a removable
runner presentation-layer surface at DS dimensions while retaining this
proven touch owner/hold/handoff. First establish display/input alignment and
safe restoration, without guest VRAM/ROM edits or save integration. Not implemented.
