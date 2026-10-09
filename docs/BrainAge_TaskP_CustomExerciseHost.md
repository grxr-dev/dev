# Task P: minimal Brain Age custom-exercise host

Date: 2026-10-09. **PASS**, using the real SDL3 Windows frontend and explicitly
classified SDL-queue input. Physical SendInput is not claimed.

## Pre-refactor responsibility map

| Responsibility | Existing implementation |
|---|---|
| Identity, gate, one-shot interception | Task J shared header initialize/before_instruction |
| Compiled callback / interpreter entry | Generic K callback, existing Tier-3 pre-step; J adapter |
| Hold safety and resume | J Hold snapshot and post-hold comparison |
| Touch ownership | Generic M setter; J installs owner |
| Contact/hit regions | M touch_state, invoked directly by J |
| Quiz answer/state | L MiniExercise, directly accessed by J |
| Native pixels and quiz drawing | N NativeSurface contains both primitives and quiz paint |
| Surface/popup lifetime | J show_surface/show_panel |
| Frontend servicing | O generic scoped callback, invoked from J hold |
| Continue decision and cleanup | J apply_action / show_surface |
| Optional controls and tracing | Mixed throughout J header |
| Window/SDL injection and capture | O frontend diagnostics and Win32 helper |

The main coupling problems are concrete quiz state/answer methods in the
lifecycle host, quiz drawing inside the surface type, contact/hit testing in
the host and a mandatory Task N capture root on cleanup. The refactor separates
these while retaining the existing generic runner facilities and historical
diagnostic protocol.

## New narrow architecture

All functional title code is ROM-free, versioned in `tools/brainage_custom/`,
namespace `brainage_custom`. The old Task J header is now only an entry-point
compatibility adapter. No generated bank, ROM, guest scene table or save logic
is changed.

| Layer | Files / facilities | Responsibilities |
|---|---|---|
| Generic runner | Existing K compiled callback, Tier-3 entry, M touch owner, N bottom presentation owner, O frontend hold service | Dispatch callbacks, consume input before guest delivery, substitute presented pixels, pump/present host-only frames |
| Brain Age host | `bc_host.h`, `bc_activation.h` | Exact title/lifecycle gate, one-shot hold, descriptor factory, instance/surface ownership, contract calls, safety checks, cleanup and natural continuation |
| Exercise contract | `bc_contract.h` | Small `Exercise` interface, owned status snapshot, touch result, descriptor/factory |
| Individual exercise | `bc_quiz.h` | Question/answer validation, local history/contact, hit regions, completion/exit permission and quiz drawing |
| Software surface | `bc_surface.h` | 256x192 ARGB8888 storage and ROM-free pixel/text primitives; no quiz state |
| Explicit selection | `bc_catalog.h` | Single static descriptor `arithmetic-2plus2`; factory creates `ArithmeticQuiz` |
| Optional adapters | `bc_diagnostics.h`, `bc_diagnostic_state.h` | Historical controls, tracing, readback/hash audits and legacy popup visualization/input |
| Reproduction | `tools/task_p/`, existing O helper | Installer, contract/config tests, bounded SDL driver, actual-window observation and audit |

The generic facilities remain unchanged in Task P. They contain no quiz answer
or title scene predicate. The host includes the catalog, but neither references
the concrete `ArithmeticQuiz` type nor contains question text, answer 4 or hit
rectangles. Replacing the factory implementation requires no lifecycle,
ownership, frontend-service or resume changes. There is one exercise, no dynamic
loading, scripting, plugin SDK or new guest menu entry.

The contract is deliberately small: `begin`, `render(Surface&)`,
`touch(x,y,down)`, and `status`. A touch result describes acceptance/change,
selected value and an exit request; status describes host-local phase/history,
completion, exit permission and contact. Status owns its phase text/history so
the final audit snapshot remains valid after instance destruction. An optional
default-no-op diagnostic action preserves historical controls; ordinary input
does not use it. A virtual destructor is sufficient cleanup; there is no save,
audio, handwriting, guest memory or SDL interface on the exercise.

The host checks exit permission rather than knowing the correct answer. It calls
render on begin and after changed exercise state; it delegates all hit testing
and validation to the exercise. A compile-time-only non-quiz mock exercises the
same contract in the unit test; it is not registered or run in Brain Age.

## Stable activation and compatibility

| Configuration | Behavior |
|---|---|
| All activation selectors absent/off | No custom instance, surface, owners, hold or panel |
| `NDS_BRAINAGE_CUSTOM_EXERCISE=1` | Enable title host; native bottom presentation defaults on |
| `NDS_BRAINAGE_NATIVE_PRESENTATION=1` | Explicit native surface choice when host enabled |
| `NDS_BRAINAGE_NATIVE_PRESENTATION=0` | Legacy separate native panel when host enabled |
| `NDS_TASK_J_CUSTOM_EXERCISE_PROBE=1` only | Compatibility activation, preserving popup default |
| Legacy J plus `NDS_TASK_N_DS_PRESENTATION=1` | Compatibility native presentation |

A present stable selector takes precedence over its corresponding legacy
selector, including an explicit `0`. Exactly `1` enables a selector. A
presentation selector alone never activates the host. Six actual environment
translation cases and pure configuration assertions passed. This is a
configuration/contract compatibility smoke, not a full rerun of Tasks J-O.

Optional historical trace/control variables remain in the diagnostic adapter.
Trace absent means record is a no-op; control absent means no file is polled;
capture root absent means no capture is required, including on handoff. The
previous mandatory capture-root failure was removed. Frontend input and the
generic service callback do not depend on these channels. With native
presentation selected, there is no separate popup. The legacy panel paints the
same exercise-provided surface and routes its local coordinates through the
shared touch abstraction instead of carrying a second quiz implementation.

## Preserved lifecycle and ownership semantics

The exact boundary is still ARM9 ARM `0x0204D790`, opcode `0xE92D4030`,
LR `0x02050268`, argument `0x41`, current/requested/selected
`0x32/0x41/0x11`, Training context `1`, exact ROM SHA-1
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

The original first instruction has not executed at interception. The synchronous
hold calls only host frontend service and exercise/adapter code; it does not run
guest CPUs, scheduler rounds or device events. Original registers, CPU counters,
Flash and scenes are checked again before returning to the untouched call.
No scene globals, stack, LR or fabricated return are written.

Cleanup order is common host logic: confirm native/guest contact clean and no
custom guest deliveries; remove touch owner; remove presentation owner;
destroy legacy panel/surface; cache final exercise status and destroy the
instance; check guest invariants; return to original instruction exactly once.
Scoped cleanup removes owners on exceptions without pretending continuation
succeeded. Close/error cancellation behavior was inspected, not dynamically
tested in this task.

## Recovery and presenter preflight

Project started at Task O commit
`15805a4c9c5f1ad562c544fca6ab69c5cd0bc2f8`; framework stays pinned at
`3a57236bb23d25dcb4caad7d58d733311062ff5e`.
The untouched checkpoint is
`local/task-g/session-001/04-training-menu/checkpoint.state`, SHA-256
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
Its normal Training menu has AAA, January 2, no active exercise. The existing
identity-validated startup restore disables inherited force-Tier-3 before
execution; it does not bypass savestate identity checks.

Early disabled preflights `local/task-p/disabled-001` through `disabled-005`
could not obtain meaningful actual-window pixels from the default Direct3D
presenter. Guest readback and frontend counters were normal, but both OS capture
methods returned uniform black. These partial attempts are preserved and are
not passing visual evidence; none started an exercise or changed the save.

The existing runner selector `NDS_SDL_RENDER_DRIVER=software` resolved the
capture problem without frontend or guest renderer changes. Task P's driver
sets this process-locally for both disabled and enabled runs. This is the normal
SDL3 game window and event mapping, not a replacement screenshot renderer.
No machine-wide configuration or graphics policy changed. Direct3D capture
behavior is not re-proven by this task. The helper can expose the exact
PID-owned window without requiring foreground focus; guarded screen fallback
checks window ownership throughout the client. Authoritative captures use
`PrintWindow`, not that fallback.

The minimal disabled control `local/task-p/disabled-006` reached ordinary rules
on the normal compiled lifecycle path, with no instance/render/owner/hold,
an actual-window capture matching guest readback, zero writes, and clean exit.
An optional observer recorded the boundary but did not intercept it.

## Reproduction and validation

Existing configured SDL3 build: `build/task-o-sdl-runner/`, adjacent `SDL3.dll`.
The installer copies owned ROM-free headers into the ignored pinned runner and
applies the already-proven generic facilities only when missing. Historical J
call sites remain thin aliases. Individual apply-patch operations avoid Windows
argument-length limits; replacing the old large owned J header uses an exact
file deletion/addition, not a recursive operation or generated-code rewrite.
Re-running the installer is idempotent.

From the checkout, with local toolchain `local/toolchain/w64devkit/bin` on PATH:

```powershell
python tools/task_p/install.py --codex-executable <installed-codex.exe>
cmake --build build/task-o-sdl-runner --target nds_runner --parallel 4
g++ -std=c++17 -Wall -Wextra -I tools/brainage_custom -I tools/task_l tools/task_p/contract_test.cpp -o build/task-p-tests/contract_test.exe -static-libgcc -static-libstdc++
python tools/task_p/check_contract.py --binary build/task-p-tests/contract_test.exe --out local/task-p/contract-check.json
python tools/task_p/drive.py --out local/task-p/new-disabled --disabled-control
python tools/task_p/drive.py --out local/task-p/new-enabled
python tools/task_p/analyze.py --out local/task-p/new-enabled
```

Use new evidence paths, never overwrite previous captures. The driver validates
the ROM and complete starting Flash, removes inherited task/stable activation
selectors, uses only stable activation for Task P, and sends explicit
session-token/sequence checked SDL queue events before frontend coordinate
mapping. Custom answers and Continue are not diagnostic choose/raw-touch calls.
Read-only sample/capture diagnostics are optional evidence instruments.

Build, focused C++ contract/mock/pixel tests, six actual configuration cases,
Python syntax checks, installer idempotence, and diff whitespace checks passed.
The old headless runner is not rebuilt: its SHA-256 remains
`19ddb95320ccca985b42ead833c5add233a3d315222dff962c21fae1e022d76c`,
its cache remains
`6dae0ee28634f24cb79412184301d2ab63b12c94a929fed4ec231c39c2593446`,
and minimal `--help` returned 0. The original separate SDL/headless modes remain
available; no broad regression matrix was run.

## Authoritative runtime and separation audit

Final authoritative evidence: `local/task-p/normal-enabled-002/`.
`normal-enabled-001/` also passed; 002 repeats the same bounded flow after the
contract's phase snapshot was made owning, rather than retaining a potentially
exercise-owned character pointer. The final source and binary are the 002 proof.
No original exercise was started in either run.

Final SDL executable SHA-256:
`35f1f7f1552a22755ee75aaab87f2742d9d3e71c138b0b3b3fabb12cee780520`.
Adjacent SDL3.dll SHA-256 remains
`4659d5a1e240e7d58fb92808f84afeb53395818cec62385d4796b72977a7d859`.

PID **221064**, HWND **21890372**, class **SDL_app**, title
**ndsrecomp firmware preview**, client **512x768**, DPI **96**. The helper
exposed this exact window at outer (40,40); client origin is (48,71).
Top client rectangle is (0,0)-(512,384); bottom is (0,384)-(512,768).
Client mapping is `(2*x, 384+2*y)`; no popup is created. The same HWND is used
for initial, Incorrect, Correct, original rules and returned-menu captures.

Only stable activation selectors were set: `NDS_BRAINAGE_CUSTOM_EXERCISE=1`
and `NDS_BRAINAGE_NATIVE_PRESENTATION=1`. The legacy activation selectors
were absent. The compiled lifecycle entry fired once for rules; normal runtime
fallback inside the original rules initializer is not a forced target fallback.

| Contract/host event | Result |
|---|---|
| Host entered, factory invoked | `arithmetic-2plus2`, one instance |
| Exercise begin/reset | Count 1; phase question; no answers |
| Host render | Counts 1/2/3 for question/incorrect/completed |
| Frontend client (108,616) -> DS (54,116) | Down/up consumed; answer 3, attempt 1, Incorrect |
| Frontend client (256,616) -> DS (128,116) | Down/up consumed; answer 4, attempt 2, completed |
| Host exit-permission queries | Six result checks, twelve tracked status queries; no quiz answer logic |
| Frontend client (256,716) -> DS (128,166) | One down/up Continue; permission from contract, exit on release |
| Cleanup/end/destruction | Ordered release of both owners and surface, instance destroyed before original resume |
| Original flow | One rules transition, one rules initializer, zero calculation constructors |
| Original Back, client (480,448) -> DS (240,32) | Two ordinary guest-owned touch deliveries; Training restored |

Authoritative actions enter `SDL_PushEvent` at the existing frontend queue
boundary, before coordinate normalization and `nds_set_touch`. No diagnostic
choose, diagnostic Continue or raw DS-touch answer call was used. Audit event
names `choose`/`continue` describe observed native results, not diagnostic input.
All six custom down/up events had guest-delivery delta zero. Native contact and
guest ADC state were released/clean before owner removal. Read-only sampling
and capture control calls are recorded separately.

Actual OS client pixels were captured through `PrintWindow` and visually
inspected. The bottom pixels at exact 2x scale match the shared native readback
and historical Task N output for each phase. RGB SHA-1:

| Phase | Actual-window/native bottom RGB SHA-1 |
|---|---|
| Initial and later initial | `ecca6be984b92e963cc84fdcbc7014c88fcbb720` |
| Incorrect | `97e88b8c2ce5b958af44c2a3b8ac408d66405289` |
| Correct | `603764477fe3a3089edd806a1a32c81d180b425e` |
| Original rules | `94d67eb1801b7b8d062e8779fc3f29de2ea002d8` |
| Returned Training menu | `9fa73ce218415464a1dbedd0c6616c990422ffce` |

Held frontend-present samples advance **7 -> 143 -> 182** while every observed
guest snapshot remains invariant: current/requested/selected **0x32/0x41/0x11**,
ARM9 cycles **2512848471**, ARM7 cycles **1256424228**, ARM9/ARM7 instruction
ordinals **218752762/73888015**, registers and Flash unchanged. Underlying raw
guest bottom SHA-1 remains `4440d6ba17dae93c0b259bf763240ec9629e4e77`;
measured VRAM A-I/palettes/OAM aggregate remains
`a13deb62d1ddb9ccb77ed7b3a6d057c7cbb45717`. Top pixels remain guest output.
No custom drawing writes guest video state.

After cleanup, current/requested become **0x41**, selected remains **0x11**.
Normal rules appear in the same real window and exactly match the disabled
control bottom capture. No-input settling retains scenes/contact with no stale
action. Normal Back returns current/requested to **0x32**; original Calculations
x20 is neither started nor completed, with no guest credit.

Complete 256 KiB Flash before/after SHA-256 is identical:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
Logical save operations **0**, Flash commits **0**, changed bytes **0**.
The process exited cleanly with code 0, no forced termination.

Machine-readable evidence remains ignored/local: `result.json`, `audit.json`,
`contract-audit.json`, compact `contract-events.json`, entry/input/native logs,
window captures, readback captures and exact saves. The architecture analyzer
checks factory/contract calls, per-instance counts, local state changes,
absence of guest/runtime references in exercise code and destruction before
resume. Optional diagnostics were enabled for this audit; diagnostic independence
is established by source inspection and no-op configuration paths, not claimed
as a separate trace-disabled gameplay test.

## Limits and next smallest experiment

This establishes a minimal title host/individual exercise seam, not a production
exercise library. No menu addition, guest scene registration, custom save/history,
Decuma, recognition, voice or cross-game plugin architecture is implemented.
Authoritative input is explicitly SDL-queue, not physical Win32 SendInput.
The custom pixels remain runner presentation pixels, never guest VRAM.

Proposed Task Q only: implement one host-local freehand canvas exercise through
the same contract to measure continuous stylus contact/motion and clean release,
without Decuma, save integration or new menu entries. **Not implemented.**
