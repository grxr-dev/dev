# Brain Age Task K: normal/compiled-path native hook parity

Date: 2026-10-09. **PASS for the target lifecycle entry on the normal execution
path.** Calculations x20 selection executes the original generated lifecycle
entry, synchronously enters the shared native state, resumes once, reaches
the identical original rules screen and returns by original Back. No exercise
started, problem answered, ROM patch, generated-C edit or save activity.

## Identity and checkpoint

Existing checkout/branch: `dev`, `codex/brainage`, starting at Task J
`7a57ea0d2515c88b2a80e5dd6d5c8d392bc1c40c`. Framework HEAD remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e` with the existing diagnostic edits
and the narrow additions below. Only the runner was rebuilt. Exact ROM SHA-1
was independently rechecked and computed by the runner:
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

All three runs restore the same untouched Task G source:
`local/task-g/session-001/04-training-menu/checkpoint.state`.
State SHA-256:
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
Starting Flash SHA-256, **H0**:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
AAA; normal Training menu; January 2, 2024, 12:00:34 guest RTC. The marker at
`0x180`, full Flash, CPU controls, both ordinals, clocks and RTC match the source.
Task G/I/J evidence was not modified.

**Important selector trap corrected:** the saved state itself contains
`force_tier3=true`; merely removing the launch argument would not test normal
execution. `restore_menu.py --normal` removes `--force-tier3` from the launch
command and, after validating the imported state without advancing it, uses
the existing `force_tier3` debug command to disable that host-only selector.
The before/after selector observations are retained in `restore.json`.
No guest RAM, register, date or save value is rewritten by this selection.
The inherited forced-miss counter is 113582860, not zero; it remains unchanged
through both normal runs. This is evidence of **zero new** forced misses.

## Actual normal backend and call boundary

The registered ARM9 bank has a dispatch entry for `0x0204D790` referring to
`brainage_arm9_main_afunc_0204D790`. The frame's generated callsite
`0x02050264` publishes original LR `0x02050268`, pushes the normal runtime
return context, charges the normal branch refill, and makes an **intra-shard
direct C call** to that function. This can bypass `runtime_dispatch_impl`.
Therefore wrapping only the top-level dispatcher would not cover this launch.

The untouched generated callee's first instruction prologue publishes
PC `0x0204D790`, checks yield, increments its ordinal, and conditionally calls
the existing `runtime_insn_slow` ABI **before** executing PUSH `0xE92D4030`.
That is the clean interception point. Target observations from the compiled-only
callback prove `backend=compiled`, `forced_tier3=false`, with exactly the Task J
PC, opcode, registers, LR, scenes, cycles and ordinals. No fallback is forced
and no dispatch lookup is replaced.

Normal execution is still a mixture of compiled banks and legitimate fallback:
the later rules initializer `0x020610B4` naturally executes through Tier-3 in
this bank inventory. That does **not** make the target lifecycle-entry proof
an interpreter proof; its entry and normal Back entry are observed directly
inside generated-bank instruction prologues. This task does not claim that
every instruction of the enclosing transition is compiled.

## Small reusable callback and shared probe

The ROM-free runtime patch is `tools/task_k/compiled-hook.patch`:

- `runner/src/io.h`: `NdsCompiledInstructionHook` and
  `nds_set_compiled_instruction_hook` expose one synchronous optional callback.
- `runner/src/io.cpp`: the armed bit includes the callback; generated
  `runtime_insn_slow` invokes it and then the unchanged trace/break payload.
- Interpreter retirement invokes only the unchanged payload, **not** a callback
  using potentially stale `g_cpu` registers. Its existing live-context pre-step
  callback remains in `tier3.cpp`.
- `runner/src/runtime_arm.cpp`: the legacy generated-bank `runtime_insn_fp`
  path still increments exactly once and invokes the compiled payload/callback.
- `runner/src/tier3.cpp`: one bounded, read-only entry observer for the same
  four addresses as the compiled observer; no instruction execution changes.

There is no subscriber registry, plugin system, generated-function rewriting,
symbol replacement, forced lookup miss, scene-table extension or guest patch.
With no activation/diagnostic trace the callback remains null, the original
armed predicates and trace/break work are unchanged, and no panel is created.
No guest instruction/cycle is charged by the callback.

`tools/task_j/brainage_native_probe.h` is shared by both paths. The initial
Task J forced-only activation rejection is removed. The actual ROM hash still
gates registration. Activation remains **`NDS_TASK_J_CUSTOM_EXERCISE_PROBE=1`**,
disabled by default. Diagnostic trace variables do not enable interception.

The compiled callback uses the live `g_cpu`; the interpreter callback uses its
live interpreter registers. Both invoke the **same** predicate, hold, native
Win32 panel, host input polling, invariant verification and normal return:

```text
ARM9 ARM; PC 0204D790; opcode E92D4030; R0=41; LR=02050268
current 020DA464=32; requested 020DA3EC=41
selected 020DA3F0=11; menu context 020DA420=1
```

The compiled host call stack, runtime BL return context and guest stack remain
live while the synchronous panel holds the emulation thread. Both CPUs, all
guest clocks and events stop; there is no guest loop under an overlay. Continue
returns into the original generated prologue and PUSH/body exactly once.
No synthetic LR return, unwind/reconstruction, cleanup skip, manually forged
scene value or result/progression credit occurs.

`install.py` applies only the owned shared header and runtime patch through
apply_patch, checks the pinned framework HEAD and is idempotent. Task J's
installer delegates the new generic support so fresh installations of its
shared header do not lack the callback declaration/implementation. The shared
context/control helpers now allow only their existing ignored Task J root or
the additional ignored Task K root.

## Authoritative disabled and enabled evidence

Roots/ports:

- `local/task-k/normal-disabled-001/`, 19865;
- `local/task-k/normal-enabled-001/`, 19866;
- `local/task-k/forced-regression-001/`, 19867.

Normal disabled control was captured first. Both normal runs select x20 once
with raw touch `(166,75)` and the same 150000000 ARM9-cycle budget. They reach
the first normal Calculations x20 rules page with original Back/More available.
No Start or instruction-page advancement was performed.

Exact compiled entry in both normal runs:

| Field | Value |
| --- | --- |
| PC / LR / CPSR | `0x0204D790` / `0x02050268` / `0x2000001f` |
| Current / requested / selected | `0x32` / `0x41` / `0x11` |
| ARM9 cycles | 2320143205 |
| ARM7 scheduler cycles | 1160071557 |
| ARM9 cycles divided by two | 1160071602 |
| ARM9 / ARM7 instruction ordinals | 209008089 / 69059507 |
| Flash SHA-1 | `a8a960103e51212efdc5bdcb5cbc28d862deb860` |
| Backend / selector | compiled / false |

Enabled event sequence is exactly:

```text
boundary_context -> intercept -> panel_active
-> held_sample -> held_sample -> continue_original
```

Two explicit host sample commands were separated by at least six seconds.
Every logged register, CPSR snapshot, scene value, both clocks/ordinals and
Flash digest remains identical through the hold and immediately before resume.
Only the lifecycle-entry observation exists during hold: the rules initializer
has not run. Current scene is still `0x32`. Both existing save traces are empty.
The panel's real native client capture was visually inspected. Original local
file timestamps place panel capture to resume at approximately **30.996 seconds**.

**Continue input provenance:** the panel resumed before the scripted
`continue 3` could be submitted; the helper correctly rejected it because the
panel was no longer waiting. The host control file remains `sample 2`.
There is one `continue_original` event. The implementation's only other exit
condition is the native Continue button's `WM_COMMAND/BN_CLICKED` handler;
there is no automatic exit. Consequently the button path is the supported
source of this Continue, rather than an accepted scripted Continue. The
individual Windows button notification was not separately logged; attribution
to that input path is reconstructed from the exclusive handlers and retained
control file. No assertion about the identity of the person pressing it is made.
No second Continue was accepted or original transition repeated.

### Equivalent normal rules state

At the identical cycle budget, normal disabled/enabled runs have **exactly
equal** captured globals, both CPU register/CPSR views, CPU/I/O counters and
controls, dispatch statistics, complete 3748-byte rules object, full Flash and
both screen image files. Both CPU views are valid. This is stronger than the
required semantic continuation equivalence; whole RAM identity is not claimed.

```text
current = requested = 0x41
selected = 0x11; menu context = 1
rules object = 0x020E9A00
calculation object = 0
rules lifecycle entry = 1
rules initializer 020610B4 with R1=41 = 1
calculation constructor 02027A28 = 0
```

The rules object/global values and screen images also match the original Task J
forced-path reference. Mode/problem count are not initialized at this boundary;
no speculative values are supplied. Normal vs forced dispatch statistics are
not expected to match because the backends differ.

### Original Back and save safety

After the enabled normal run reached rules, original Back was tapped once at
`(240,32)` and allowed the same 150000000-cycle settling budget. The normal
Training menu returns with current/requested `0x32`, selected `0x11`, menu
context 1 and null calculation object. The x20 button remains selectable;
no exercise started or completed. There is one additional lifecycle entry
for Back, distinct from the single original rules transition.

All disabled/enabled phases have **zero logical write APIs, Flash commits,
accepted bytes and changed bytes**, with before/after SHA-256 H0. Existing
Task C request tracing remains active for interpreter execution; the new
compiled-only entry observer additionally counts the known logical write API
`0x0200DE78`, so a compiled request cannot disappear from the zero-write claim.
Physical Task A tracing remains active regardless of backend. Independent
old-byte replay agrees with live Flash, phase snapshots and the copied disk save.

## One forced-Tier-3 regression

Performed **only after** the normal-path hold/resume/Back succeeded. Restore the
same checkpoint, retain forcing, select x20 once, take one held sample, supply
one explicit `continue 2` through the shared host-input channel and observe
normal rules. Backend is Tier-3 at the target and the same invariant context is
preserved. Rules appear normally, with one lifecycle/init and zero calculation
constructors. Rules globals/object and screen files match both normal runs.
No extra Back run, long hold suite, problem input or exercise completion.
The single regression also has unchanged H0 and empty save traces.

## Commands, validation and artifacts

```powershell
python tools/task_k/install.py --codex-executable <bundled-codex.exe>
$env:PATH="$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-a-runner --target nds_runner --parallel 2
python tools/task_k/launch.py --out local/task-k/normal-disabled-001 --port 19865
python tools/task_g/capture.py --out local/task-k/normal-disabled-001 --label 00-menu --cycles 0 --savestate
python tools/task_j/context.py --out local/task-k/normal-disabled-001 --name menu
python tools/task_g/capture.py --out local/task-k/normal-disabled-001 --label 01-select-x20 --tap 166 75 --cycles 150000000 --savestate
python tools/task_j/context.py --out local/task-k/normal-disabled-001 --name rules
python tools/task_k/launch.py --out local/task-k/normal-enabled-001 --port 19866 --enabled
```

Capture enabled `00-menu`/menu context identically; run `01-select-x20`
asynchronously because its debug request blocks in the synchronous native state.
Use shared `control.py --out ... --action sample --sequence 1`, wait at least
six seconds, sample sequence 2, then supply one Continue through the visible
button or host input. Never send a second Continue after the visible button
has already resumed. Capture rules context; then capture `02-normal-back`
with `(240,32)` and 150000000 cycles, and `returned-menu` context.

```powershell
python tools/task_k/launch.py --out local/task-k/forced-regression-001 --port 19867 --enabled --forced-regression
python tools/task_g/capture.py --out local/task-k/forced-regression-001 --label 01-select-x20 --tap 166 75 --cycles 150000000 --savestate
python tools/task_j/control.py --out local/task-k/forced-regression-001 --action sample --sequence 1
python tools/task_j/control.py --out local/task-k/forced-regression-001 --action continue --sequence 2
python tools/task_j/context.py --out local/task-k/forced-regression-001 --name rules
python tools/task_k/analyze.py --root local/task-k
```

The regression capture likewise runs asynchronously while held. Use new output
names; existing evidence is never overwritten. The analyzer's authoritative
run names match this task's three named roots.

Runner build passed (`local/task-k-build.log`); existing unused frontend-function
warnings remain unrelated. No generated-bank build/emission, coverage tuning,
benchmark matrix or unrelated tests. Python syntax checks, both installer
idempotence checks and the bounded analyzer passed. Only the three explicitly
requested gameplay runs occurred. All three identity-verified paused runner
PIDs were stopped after loadable checkpoints/evidence were preserved.

ROM-free changes: this report; `tools/task_k/{compiled-hook.patch,install.py,
launch.py,analyze.py}`; normal selector option in `tools/task_i/restore_menu.py`;
shared Task J header/installer and root validation in its context/control helpers.
Ignored runtime edits are the installed header plus `io.h`, `io.cpp`,
`runtime_arm.cpp`, `tier3.cpp`; existing Task A-J integration remains intact.

Local artifacts: each run's `restore.json`, `session.json`, `native-probe.jsonl`,
`entries.jsonl`, phase images/saves/states/summaries, CPU/scene contexts;
`normal-enabled-001/hold-proof.json` and `native-panel.bmp`;
`local/task-k/proof-audit.json`; `local/task-k-launch-*.log`.
ROM, save, state, image, generated code and raw trace outputs remain ignored.

Normal sandbox creation actually failed again with
`helper_unknown_error: setup refresh had errors`. Supported per-operation
outside-sandbox execution worked through auto-review without human approval
prompts. No blanket/full access or approval/relay policy changes were made.

## Conclusion and smallest future Task L

**Proven:** the same title-specific native state safely intercepts a genuinely
compiled lifecycle entry on normal execution and the original interpreter entry
on forced execution, holding the live call context and resuming once. Original
rules/Back and unchanged save semantics are preserved. The generic compiled
prologue callback covers direct calls, not just dispatcher entries.

**Not proven:** every game instruction compiling, all title/scene hooks,
cross-platform UI, new exercise IDs, result/save ABI, or original guest
recognition while the native state freezes the guest. No real custom exercise
or menu entry was added; touch/recognition/render/audio/RTC/save systems remain
original facilities, not replacement projects.

Recommended smallest Task L: add one trivial host-side answer/choice interaction
inside the existing held state, then resume original rules and Back with zero
guest result/save credit. Keep the same boundary and original continuation;
do not add a scene/menu ID or save format. This proposal is not implemented.
No unresolved runtime blocker remains for Task K. Task L was not begun.
