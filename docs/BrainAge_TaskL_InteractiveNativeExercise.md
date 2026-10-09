# Brain Age Task L: first interactive custom native mini-exercise

Date: 2026-10-09. **PASS on normal execution at the compiled lifecycle entry.**
The inserted native state asks `2 + 2 = ?`, accepts the explicit diagnostic
sequence **3 -> 5 -> 4**, retains two incorrect attempts, completes only on 4,
and resumes untouched Brain Age only after one explicit Continue. Original
rules and Back work normally. No guest exercise, progression credit or save
operation occurred. UI/input/result state are host-native, not guest integration.

## Recovery and baseline control

Existing checkout/branch: `dev`, `codex/brainage`, beginning at Task K
`9e1dc3e97112ea1ca0dd268ca23f92880e073724`. Framework HEAD remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`, with the established local diagnostic
integration. Exact ROM SHA-1 is verified by launcher, runner and independently:
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

Reused unchanged Task G `local/task-g/session-001/04-training-menu/checkpoint.state`
and Task K's `local/task-k/normal-disabled-001/` reference. Checkpoint SHA-256:
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
AAA; January 2, 2024, 12:00:34 guest RTC; normal Training menu. Starting Flash
SHA-256, **H0**, is:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Task K reference images/state/logs are readable. A local integrity manifest
records their hashes and the source checkpoint; the final analyzer confirms
they remain unchanged. The callback, title gate, disabled early return,
scheduler and original continuation were not changed. Changes concern only
the opt-in host panel/state/input, diagnostic fields and installation support;
therefore no fresh disabled gameplay control was needed. Resumed rules are
compared directly against the validated Task K disabled reference.

Normal launch omits `--force-tier3`. Following Task K, after loading and
validating the source state, the existing debug selector disables the inherited
forced flag **before execution**. Its inherited miss counter 113582860 remains
unchanged. At the target, compiled-only callback observations explicitly report
`backend=compiled`, `forced_tier3=false`. Rules initialization itself naturally
uses fallback as previously established; not every transition instruction is
claimed to be compiled.

## Host-only implementation

Activation remains **`NDS_TASK_J_CUSTOM_EXERCISE_PROBE=1`**, disabled by default.
The activated blank Continue-only J/K panel is now intentionally superseded
by this quiz; the original guest hook and return semantics are unchanged.

`tools/task_l/mini_exercise_state.h` defines:

- `MiniExercise`: question/incorrect/completed/resuming phase, answer history,
  derived attempt count, completed flag, choice validation and guarded resume.
- `ControlOrder`: per-instance session identity and strictly consecutive,
  positive command numbers; stale session and replay/order rejection.

Only 3, 4 and 5 are choices. Wrong answers append history and remain incorrect;
4 completes the host state. No additional choice is accepted after completion.
Resume is rejected unless completed and can succeed only once. These values
live on the native stack/heap; none is written into guest RAM or Flash.

The shared `tools/task_j/brainage_native_probe.h` displays the prompt, three
native buttons, answer/attempt history and incorrect/correct indication.
Continue is disabled until completion. After correct, choices are disabled
and Continue is enabled. Both GUI and diagnostic inputs use the same validator.
Window close is not Continue; no answer or exit is timer-driven. The host timer
only polls explicitly supplied commands. Native state is destroyed when the
callback returns normally, before original guest instruction execution resumes.

The exact gate is unchanged:

```text
verified ROM; ARM9 ARM; PC 0204D790; opcode E92D4030; LR 02050268
current 020DA464=32; requested 020DA3EC=41
selected 020DA3F0=11; Training context 020DA420=1
```

The callback is still before the original lifecycle PUSH/cleanup/init, keeping
the actual compiled C stack and guest BL context intact. It does not yield,
unwind, reconstruct a return, change guest registers, substitute scenes,
call guest save/scoring APIs or add a menu/scene-table entry.

## Session-safe explicit control

Runner-owned file protocol:

```text
SESSION SEQUENCE sample
SESSION SEQUENCE choose ANSWER
SESSION SEQUENCE continue
```

The session token combines host steady-clock observation and process identity
at interception; it does not change guest RTC or RNG. Fresh output roots plus
token matching prevent old controls from influencing a new run. The native
reader accepts only the next positive sequence for the current session;
unchanged-file polling does nothing. Accepted command numbers are consumed
once, even when semantic validation rejects the action, so rejection is
acknowledged and the next explicit command can proceed. Invalid session/order
does not advance the sequence. Malformed/unknown actions are rejected.

`tools/task_j/control.py` atomically publishes one command and waits for its
matching diagnostic acknowledgement. It validates session/sequence/phase;
`--expect-rejected` deliberately tests runtime rejection instead of silently
bypassing validation. A repeated Continue after resume is rejected before any
file publication. Log fields distinguish `diagnostic` from `native_ui` input.

The authoritative proof uses **only** the diagnostic channel. No Graham click
is required or accepted as proof. `drive.py` supplies the exact authorized
choices; it does not inject guest input, answers, profile state or result data.
Its six-second host wait proves persistent hold, not an automatic panel exit.

## Authoritative interaction and freeze evidence

Final authoritative run: **`local/task-l/normal-enabled-002/`**, port 19869.
One normal x20 tap `(166,75)`, then the following explicit host commands:

| Control sequence | Action | Host result | Attempts | Continue |
| ---: | --- | --- | ---: | --- |
| 1 | sample | question; no answers | 0 | unavailable |
| 2 | choose 3 | incorrect; history `[3]` | 1 | unavailable |
| 3 | continue | rejected: `not_completed` | 1 | unavailable |
| 4 | choose 5 | incorrect; history `[3,5]` | 2 | unavailable |
| 5 | continue | rejected: `not_completed` | 2 | unavailable |
| 6 | choose 4 | correct/completed; history `[3,5,4]` | 3 | available |
| 7 | sample | still completed; Brain Age still held | 3 | available |
| 8 | continue | accepted once; original transition resumes | 3 | consumed |

Every input/result row is sourced `diagnostic`; no `native_ui` action appears.
The runtime records 15 compact custom events in exact order:

```text
interception context -> intercept -> panel active -> initial held sample
-> choose 3 -> incorrect -> premature Continue rejected
-> choose 5 -> incorrect -> premature Continue rejected
-> choose 4 -> correct/completed -> post-completion held sample
-> Continue -> continue_original
```

Every event preserves the identical guest invariant:

| Field | Frozen value |
| --- | --- |
| current / requested / selected | `0x32` / `0x41` / `0x11` |
| ARM9 cycles | 2320143205 |
| ARM7 scheduler cycles | 1160071557 |
| ARM9 / ARM7 instruction ordinals | 209008089 / 69059507 |
| CPSR snapshot | `0x2000001f` |
| Flash SHA-1 | `a8a960103e51212efdc5bdcb5cbc28d862deb860` |

All sixteen registers and nonterminal state also match. Initial to completed
held sample spans **6.052294 host seconds**. Panel capture to actual resume is
approximately 24.135 host seconds by original file timestamps. The only
entry observation before Continue is the held lifecycle entry: no rules init.
Both save traces remain empty. Both guest CPUs/clocks are frozen throughout;
this is not an overlay while the game continues underneath.

Actual native captures were visually inspected: initial question, both wrong
states with choices/disabled Continue visible, and correct state with enabled
Continue. Files are `native-panel.bmp.{3,6,9,12}.bmp` in the authoritative root.
They are real native-client renders, not edited or synthesized screenshots.

## Original continuation, Back and save safety

After command 8, the original transition executes exactly once. Stable rules
are reached at the same 150000000-cycle budget as Task K. Captured complete
rules context, both CPU register/CPSR views, I/O counters/controls, dispatch
statistics, 3748-byte rules object, both image files and full Flash match the
disabled reference **exactly**. Current/requested are `0x41`, selected `0x11`,
menu context 1, rules object `0x020E9A00`, calculation object null. Rules init
count is 1; calculation constructor count is 0. No duplicate init or invalid
dispatch/stack/register state was observed.

Original Back is tapped once at `(240,32)` and settled for 150000000 cycles.
Normal Training returns: current/requested `0x32`, selected `0x11`, context 1,
null calculation object and x20 still selectable. No More/Start, original
answer, exercise completion or guest credit. A second Continue request is
explicitly rejected without changing the control file.

Across menu, quiz, rules and Back: **0 logical save requests, 0 Flash commits,
0 accepted bytes, 0 changed bytes**. All full before/after snapshots hash to
H0. Existing physical Flash tracing and both logical API backends remain
observed; the known write API never appears. Independent old-byte replay
matches live Flash and the unchanged copied battery file.

`audit.json` has 18 compact entries: 15 runtime custom events, plus derived
rules-reached, Back-action and menu-restored checkpoints. Derived entries are
labeled as such, not represented as extra raw hook callbacks. Every custom
action carries sequence, phase, attempts, answer/history, completed/Continue
flags, input source, scenes, both counters/ordinals and Flash digest.

## Validation and preserved iteration history

Pure host `state_test.cpp` passed: wrong/correct history, invalid answer,
premature/duplicate Continue, stale session and sequence replay/order.
Runner build, Python syntax checks, both installer idempotence checks and the
compact independent analyzer passed. No generated-bank emission/edit/build,
coverage optimization, benchmark matrix or unrelated test repair.

First run `normal-enabled-001/` passed interaction/freeze/resume/Back/save
checks, but visual QA showed parent repaint obscuring buttons after wrong
answers. It is preserved untouched. The narrow fix redraws all native child
controls, and only this requested proof was repeated in `normal-enabled-002/`.
Wrong/correct captures now show all controls correctly. No original exercise
was started in either run; both identity-verified paused runner PIDs were stopped
after saved checkpoints. No other gameplay route was replayed.

Initial build warned about new aggregate fields; explicit default initialization
removed those warnings. Installing the enlarged shared header initially hit
Windows `WinError 206` because full-file replacement exceeded command length.
Installer now emits small apply_patch hunks via `difflib`; final source equality
and idempotence are verified. Logs `local/task-l/build*.log` preserve build
history; the failed installer did not lead to a gameplay run with stale code.

No forced-Tier-3 regression was necessary: neither backend callback nor original
continuation changed, and both paths use this same host-only state/UI/control.
Task K's prior forced-path proof and artifacts remain unchanged; no new
interpreter-path mini-exercise result is claimed.

## Reproduction, files and artifacts

```powershell
python tools/task_k/install.py --codex-executable <bundled-codex.exe>
$env:PATH="$PWD/local/toolchain/w64devkit/bin;$env:PATH"
g++ -std=c++17 -Wall -Wextra -Itools/task_l tools/task_l/state_test.cpp -o local/task-l/state-test.exe
local/task-l/state-test.exe
cmake --build build/task-a-runner --target nds_runner --parallel 2
python tools/task_k/launch.py --out local/task-l/normal-enabled-002 --port 19869 --enabled
python tools/task_g/capture.py --out local/task-l/normal-enabled-002 --label 00-menu --cycles 0 --savestate
python tools/task_j/context.py --out local/task-l/normal-enabled-002 --name menu
```

Run `capture.py --label 01-select-x20 --tap 166 75 --cycles 150000000 --savestate`
asynchronously: the debug request remains busy during the native hold.
Then explicitly run `tools/task_l/drive.py --out ...` to issue only the approved
sequence and Continue, await the capture, collect rules context, and capture
Back with `(240,32)`. Collect `returned-menu` context. Do not press Start.
The shared control CLI also supports each action separately with `--action
choose --answer 3 --sequence 2`, etc.; premature tests use `--expect-rejected`.
Use new output names rather than overwriting evidence.

```powershell
python tools/task_l/analyze.py --out local/task-l/normal-enabled-002
```

ROM-free changed files:

- `docs/BrainAge_TaskL_InteractiveNativeExercise.md`;
- `tools/task_l/mini_exercise_state.h`, `state_test.cpp`, `drive.py`, `analyze.py`;
- `tools/task_j/brainage_native_probe.h`, `control.py`, `context.py`;
- `tools/task_k/install.py`, `launch.py`.

The installer copies only the two owned headers into ignored runner source;
Task K's generic callback implementation is unchanged. Context/launch roots
add the ignored Task L directory. No ROM/generated-C/save semantics changes.

Local-only artifacts: `local/task-l/normal-enabled-002/` contains the 18-event
`audit.json`, `interaction-proof.json`, `controls.json`, diagnostic logs,
`duplicate-continue-rejection.json`, native captures, checkpoint contexts,
phase saves/images/states/summaries. `normal-enabled-001/` preserves the first
render iteration. Reference integrity, build/launch logs and host test binary
remain under `local/task-l/`. All artifacts are ignored; no raw data, saves,
states, screenshots, ROM/extracted/generated binaries/C are staged.

Normal sandbox creation actually failed with
`helper_unknown_error: setup refresh had errors`. Supported per-operation
outside-sandbox execution worked through auto-review without Graham approval
prompts. No sandbox/approval/relay policy or host OS clock was changed.

## Conclusion and smallest future Task M

**Proven:** a real interactive host-native quiz loop runs while Brain Age is
frozen, keeps wrong-answer state, validates completion and explicitly resumes
the untouched compiled lifecycle once, followed by original rules/Back and no
save/progression side effects. Authoritative inputs are machine-controlled,
not inferred human clicks.

**Not proven:** DS-rendered custom UI, DS touch routing, Decuma/voice reuse,
guest result/history/save integration, new Training menu entries or custom
scene registration. The host result is not a Brain Age result.

Recommended smallest Task M: route the runner's existing touch input into this
same native choice state while preserving the guest hold and original return;
no handwriting, new scene/menu, scoring or save integration. That input bridge
needs its own bounded feasibility proof and is **not implemented here**.
No unresolved Task L blocker. Task M was not begun.
