# Brain Age Task J: first native custom-state hook proof

Date: 2026-10-09. **PASS on the existing forced-Tier-3 execution path.**
One normal Calculations x20 launch enters an actual synchronous native state,
holds the original lifecycle transition, accepts one deliberate Continue,
resumes the untouched guest instruction, and returns via the game's Back.
No exercise started, answers, save activity, ROM patch or generated-C edit.
This does not establish interception of compiled guest banks or a real exercise.

## Baseline, recovery and a necessary Task I correction

Existing checkout/branch: `dev`, `codex/brainage`, starting at
`5758b28ed5ac24cc9e7b6be0d9d0371daecbf82d`. Framework HEAD remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`; only the narrow local integration
described below is added to existing A/C/I/F diagnostics. Existing direct boot,
FreeBIOS/generated firmware, network-off, headless debug server configuration
and guest RTC remain unchanged. Only the runner was rebuilt.

Exact ROM SHA-1 is checked by the launcher and independently computed by the
runner: `b8a105bacc3234dede8d4465df0869f2b922a0e2`. The hook uses the runner's
actual computed hash, not an environment-provided assertion.

Both authoritative runs independently restore the same Task G source:
`local/task-g/session-001/04-training-menu/checkpoint.state`.
State SHA-256:
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
Starting Flash SHA-256, **H0**:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
AAA; January-2 normal Training menu; `CLEAR-RAM-CHECK` at `0x180`.
Guest RTC: 2024-01-02 12:00:34. ARM9 cycles/instructions 2280424860 / 206817686;
ARM7/system cycles/instructions 1140212430 / 68005876. Restoration verifies
CPU controls, both ordinals, RTC and complete Flash against the source.
All Task G/I evidence is preserved.

**Correction, proven dynamically:** this Daily Training menu's current scene
is **`0x32` (50)**, not 3. Task I's lifecycle call record already contained
R1=`0x32` and R4=3; the frame code loads current scene into R1 before its
desired/current comparison. R4=3 was not the current-scene global. Task J
directly observes `0x020DA464=0x32` at entry and restores the menu with that
same value after normal Back. The semantic gate is therefore:

- actual ROM identity;
- ARM9 ARM, PC `0x0204D790`, exact original PUSH opcode `0xE92D4030`;
- R0=`0x41`, original LR=`0x02050268`;
- current `0x020DA464=0x32`;
- requested `0x020DA3EC=0x41`;
- selected `0x020DA3F0=0x11`;
- Training-menu context `0x020DA420=1`.

This is the same real x20 selection boundary, not forged scene values or a
different route. Task I's report includes an explicit erratum and corrected
future-hook gate. No new broad state-machine investigation was performed.

The first disabled capture `disabled-001` revealed the old-scene mismatch and
is preserved, not overwritten. After correcting the predicate, the complete
disabled control was captured in `disabled-002` **before** the enabled run.
Both showed normal rules and zero saves. No enabled gameplay retry was needed.

## Implementation: synchronous host state, no continuation reconstruction

Activation: **`NDS_TASK_J_CUSTOM_EXERCISE_PROBE=1`**, disabled by default.
The current proof explicitly requires `--force-tier3`; requesting activation
on another execution path is rejected rather than silently claiming coverage.
Wrong ROM identity is likewise rejected. A one-shot process-local flag prevents
re-interception of the same transition.

ROM-free implementation: `tools/task_j/brainage_native_probe.h`.
The installer applies that header and these narrowly scoped runner changes:

- `runner/src/main.cpp`: include; initialize from computed `rom_sha1`.
- `runner/src/tier3.cpp`: include; condition-passed pre-step callback.
- `runner/CMakeLists.txt`: Windows `user32`/`gdi32` linkage.

The callback runs at **the first instruction of `0x0204D790`**, after the
original BL has naturally set LR and branched, but **before the original PUSH,
cleanup, allocation or rules initialization executes**. The interpreter's
instruction ordinal has already been charged as an instruction begins; no
extra guest instruction or cycle is charged by the hook.

The native panel's Windows message loop runs **synchronously on the active
emulation thread** inside that callback. The interpreter's live CPU context,
original host stack and guest BL/return context remain in place. No scheduler
round, CPU step, system event or guest clock tick runs during the native state.
Only native painting and host-input polling occur. This intentionally freezes
both guest CPUs; it is not an overlay with the game running underneath.

Continue exits the panel loop. The callback verifies the saved sixteen guest
registers, both CPU ordinals/cycles, Flash digest, scene values and nonterminal
state remain unchanged. It then returns normally to the **existing single
`Interpreter::step`**, which executes the original PUSH/body/return unchanged.
There is no breakpoint unwind, LR synthesis, host-return reconstruction,
guest PC/register write, manual scene setter, skipped cleanup or fake completion.

Native content: "Brain Age Native Hook Test", "Custom exercise slot reached",
"Guest transition held until Continue", and one
"Continue to Calculations x20" button. Window close is not a resume action.
There is no timer/automatic exit. A 50 ms host timer only polls diagnostic input.

The visible button handles `WM_COMMAND/BN_CLICKED`. This test supplied Continue
through the panel's purpose-built diagnostic host-input channel, using
`control.py --action continue --sequence 3`; it sets the same held-state exit
condition, not guest state. `sample` commands observe without resuming. Fresh
isolated output directories prevent stale control input. GUI screenshot
automation was unnecessary: the panel exports its actual native client drawing
with `PrintWindow` to a local BMP. No external UI manipulation was used.

When activation and diagnostic tracing are absent, the callback returns
immediately and no panel, interception or probe artifact is created. Disabled
trace mode is read-only and observes the boundary without holding it.

## Disabled reference and enabled proof

Authoritative roots:

- `local/task-j/disabled-002/`, port 19855;
- `local/task-j/enabled-001/`, port 19856.

Both use raw x20 tap `(166,75)` and the same 150000000 ARM9-cycle budget.
The disabled run reaches the first normal rules screen: Calculations x20
instruction text, original examples, **Back and More enabled**.
Its final CPU/I/O and both screen images also exactly match the pre-Task J
Task I `x20-001/01-select-x20` evidence.

Actual boundary in both runs:

| Field | Value |
| --- | --- |
| ARM9 PC / original opcode | `0x0204D790` / `0xE92D4030` |
| original return LR | `0x02050268` |
| current / requested / selected | `0x32` / `0x41` / `0x11` |
| ARM9 cycles | 2320143205 |
| system cycles | 1160071602 |
| ARM7 scheduler cycles | 1160071557 |
| ARM9 / ARM7 instruction ordinals | 209008089 / 69059507 |
| CPSR | `0x2000001f` |
| Flash SHA-1 during hold | `a8a960103e51212efdc5bdcb5cbc28d862deb860` |

Enabled event order, exactly:

```text
1 boundary_context
2 intercept
3 panel_active
4 held_sample         explicit sample 1
5 held_sample         explicit sample 2, at least six host seconds later
6 continue_original   explicit Continue 3
```

At both held samples, every logged register, CPSR, scene value, both CPU
ordinals/cycles and Flash digest is identical to boundary entry. Logical and
Flash trace files are empty. Current scene is still menu `0x32`, not rules
`0x41`; the original lifecycle PUSH has not executed. This proves a persistent
native state holding the transition, not a one-frame visual overlay. The real
panel capture is `enabled-001/native-panel.bmp` and was visually inspected.
Original local file timestamps place panel capture to final Continue log at
approximately **50.516 host seconds**; the two explicit samples alone provide
the controlled six-second minimum. Neither interval advances guest time.

There is exactly one interception and one Continue. After Continue, normal
rules appear. Both runs execute exactly one rules initializer
`0x020610B4` with R1=`0x41` and one original lifecycle call for rules.
Calculation constructor `0x02027A28` is called **zero times**: no Start or
countdown/problem session was entered.

### Equivalent stable state

At the identical cycle budget, reference and resumed runs have **exactly
matching** captured globals, both complete CPU register/CPSR snapshots,
CPU/I/O counters/controls, dispatch statistics and the 3748-byte rules object.
Both captured screen-image files are byte-identical. Flash is byte-identical.
Matching globals:

```text
current = requested = 0x41
selected = 0x11
menu context = 1
rules object = 0x020E9A00
calculation object pointer = 0
```

Calculation mode/problem count are not initialized at this rules boundary;
they are not fabricated or inferred from the unrelated rules-object layout.
The actual matching state is stronger than semantic equivalence, although
whole-RAM identity and host wall-time/profile counters are not claimed.

## Normal return and save safety

From the resumed first rules page, the original visible **Back** was tapped
once at raw `(240,32)`, followed by 150000000 ARM9 cycles. The original
January-2 AAA Training menu returns, with x20 still normally selectable.
Current/requested scene return to `0x32`; selected scene remains `0x11`;
calculation object is still null. No More, Start, calculation answer, Reading,
picture drawing, date change or second exercise was performed.

| Phase | Logical save APIs | Flash commits | Changed bytes | Flash hash |
| --- | ---: | ---: | ---: | --- |
| disabled menu -> rules | 0 | 0 | 0 | H0 |
| enabled menu -> native hold | 0 | 0 | 0 | H0 |
| Continue -> original rules | 0 | 0 | 0 | H0 |
| original Back -> Training menu | 0 | 0 | 0 | H0 |

All full Flash before/after snapshots hash to H0. Existing A/C observers
remain active throughout. Independent phase replay matches live Flash and
the unchanged copied save. No persistent state or exercise credit was awarded.

## Reproduction and validation

```powershell
python tools/task_j/install_probe.py --codex-executable <bundled-codex.exe>
$env:PATH="$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-a-runner --target nds_runner --parallel 2
python tools/task_j/launch.py --out local/task-j/disabled-002 --port 19855
python tools/task_g/capture.py --out local/task-j/disabled-002 --label 00-menu --cycles 0 --savestate
python tools/task_g/capture.py --out local/task-j/disabled-002 --label 01-select-x20 --tap 166 75 --cycles 150000000 --savestate
python tools/task_j/context.py --out local/task-j/disabled-002 --name rules
python tools/task_j/launch.py --out local/task-j/enabled-001 --port 19856 --enabled
python tools/task_g/capture.py --out local/task-j/enabled-001 --label 00-menu --cycles 0 --savestate
python tools/task_j/context.py --out local/task-j/enabled-001 --name menu
```

Run enabled `capture.py --label 01-select-x20 --tap 166 75 --cycles 150000000
--savestate` asynchronously: it deliberately blocks while the probe is active.
Supply explicit `control.py --out ... --action sample --sequence 1`, wait at
least six host seconds, then sample sequence 2. Inspect the panel/held evidence.
Supply exactly one `--action continue --sequence 3`, await the original capture,
and collect rules context. Then capture `02-normal-back` with `(240,32)` and
collect `--name returned-menu`. Do not Start or answer anything.

```powershell
python tools/task_j/analyze_probe.py --disabled local/task-j/disabled-002 --enabled local/task-j/enabled-001 --output local/task-j/proof-audit.json
```

Use new output names for a new proof, never overwrite existing evidence. The
input sample/Continue sequence is explicit, not automatically sent by a timer
or launcher. The debug command is busy during the synchronous hold, so use
the purpose-built host control channel rather than reentering the emulator.

Runner build passed; installer idempotence, Python syntax checks and the
independent proof analyzer passed. Initial build exposed a new-code Unicode
cursor resource type mismatch; fixed with the explicit wide resource ID.
Logs `local/task-j-build.log`, `task-j-build-002.log`, `task-j-build-003.log`
preserve that history. No broad tests, benchmark matrix or extra exercise run.
Both verified paused runner PIDs were stopped after their loadable checkpoints
and proof evidence were preserved. The headless runner has no frontend quit;
no persistence/relaunch experiment was required by this task.

ROM-free files: this report, Task I erratum, and `tools/task_j/` header,
installer, launcher, host control, read-only context and analyzer scripts.
Ignored runtime edits: `local/ndsrecomp/runner/src/{main.cpp,tier3.cpp,
brainage_native_probe.h}` and `runner/CMakeLists.txt`. No generated C/bank edit.
Local raw captures, saves, states, images and traces remain under `local/task-j/`.
Derived validation: `local/task-j/proof-audit.json`; hold evidence:
`enabled-001/hold-proof.json`; before/after state evidence in each phase.

Normal sandbox process creation still actually failed with
`helper_unknown_error: setup refresh had errors`. Supported per-operation
outside-sandbox execution worked through auto-review, without human prompts
or approval infrastructure changes. Native UI plugin initialization also
failed (`trusted Node process exited unexpectedly`); this did not block the
runner's own native panel capture/host-input facility.

## What is proven, limits and recommended Task K

**Proven:** a ROM-free native C++ custom state can occupy the exact x20 launch
boundary, hold both CPUs indefinitely until deliberate Continue, preserve the
live call context, resume the original transition once, and return normally
without saving or editing game code. The feature is opt-in and disabled behavior
matches prior evidence.

**Not proven:** normal compiled-bank interception, portable frontend integration,
an actual custom exercise/result/save ABI, concurrent guest recognition while
the native state is active, generalized plugins, or new scene/menu entries.
The current panel is Windows-only and freezes all guest execution; original
touch/Decuma/rendering/audio/RTC/save systems have not been replaced.

Recommended smallest Task K: expose the **same** callback safely on the normal
compiled/interpreted execution paths and repeat only this launch/Continue/Back
proof without forced Tier-3. Verify the actual path and continuation semantics;
do not add exercise logic, score/save integration or menu entries yet.
Task K was not started. No unresolved blocker for this bounded Task J proof.
