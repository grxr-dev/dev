# Task O ? Windows frontend presentation/input prerequisite

## Result: blocked, not a frontend PASS

The available runner was built **without SDL**. One isolated `--interactive`
startup returned exit code **1** and the exact error:

```text
[sdl] this runner was built without SDL; configure NDS_SDL_BACKEND=SDL3 or SDL2 for interactive presentation
```

No SDL game window was created. No custom answer, Continue, or Back input was
sent. Task N's headless/readback proof is not substituted for a Windows proof.
This is the task's explicitly permitted unavailable-frontend blocker, not a
claim that Windows frontend support is impossible to build.

Project starting revision: `7315693514bcfefe907947fbe2ca3281caaac953` (Task N).
Framework revision remains `3a57236bb23d25dcb4caad7d58d733311062ff5e`.
No dependency, framework, frontend, hold-loop, or generated-bank changes were
made for this result.

## Recovery and execution

The prior references remain intact:

- Task N: `local/task-n/normal-enabled-002/`.
- Task G menu reference: `local/task-g/session-001/04-training-menu/checkpoint.state`.
- Task G menu save: `local/task-g/session-001/04-training-menu/after.sav`.

The probe verified the ROM SHA-1 as
`b8a105bacc3234dede8d4465df0869f2b922a0e2`, copied only the menu save into a
new ignored directory, and used the Task N normal launch command with
`--serve` replaced by `--interactive`. Both J and N selectors and January-2
RTC control were enabled. No `--force-tier3` argument was supplied.

**The runtime menu checkpoint was not restored:** interactive startup failed
before a frontend event/scheduler loop existed. Configured compiled banks were
registered, but execution of the target compiled lifecycle boundary was not
tested. No claim of a Task O normal-path hold is made.

Before and after save SHA-256:

```text
a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb
```

The complete 262144-byte images match. Changed bytes: **0**. Flash, logical
request, and call trace files each contain **0 lines**. These observations
apply only to the failed interactive-startup probe, not to the unperformed
Task O interaction sequence.

## Prepared build and dependencies

`build/task-a-runner/CMakeCache.txt` records:

```text
NDS_SDL_BACKEND:STRING=NONE
NDS_ENABLE_COMPUTE_RENDERER:BOOL=OFF
```

The runtime message independently confirms SDL is absent from the executable;
the finding is not based only on a possibly stale cache. No SDL2/SDL3 package
config or DLL was found in the prepared `local/toolchain` tree. Checked standard
MSYS2 SDL locations and SDL/CMake/vcpkg environment hints were also absent.
This was a bounded local prerequisite check, not an exhaustive machine-wide
search. SDL acquisition or a new SDL-enabled build was not attempted.

## Narrow source map

All observations here describe inspected source, **not live-window evidence**.
Paths below are in the ignored framework integration unless stated otherwise.

| Boundary | Location | Role |
| --- | --- | --- |
| Interactive entry | `runner/src/main.cpp:2287` | Starts debug pump, invokes frontend, flushes saves on exit. |
| SDL frontend | `runner/src/frontend.cpp:2023` | Normal interactive event/render loop when SDL is compiled in. |
| Missing-SDL stub | `runner/src/frontend.cpp:4189` | Reports prerequisite error and returns 1. |
| Logical conversion | `runner/src/frontend.cpp:1508` | Converts frontend mouse event coordinates before DS mapping. |
| DS touch mapping | `runner/src/frontend.cpp:936` | Bottom hit check, subtract origin, clamp to DS coordinates, call `nds_set_touch`. |
| Event pump | `runner/src/frontend.cpp:3018` | `SDL_PollEvent`, then ordinary coordinate conversion/handling. |
| Guest work | `runner/src/frontend.cpp:3761` | Scheduler rounds on the frontend thread. |
| Bottom presentation | `runner/src/frontend.cpp:3810` | Reads Task N's shared presented framebuffer, then SDL texture/presentation path. |
| Native hold | `tools/task_j/brainage_native_probe.h:377` | Owned surface/touch state; polls existing host control and sleeps. |

Guest/native surfaces use the existing 32-bit screen-pixel representation;
Task N owns an ARGB8888 256x192 bottom surface. Normal frontend extraction
uses the shared presentation getter, so the N override is source-integrated
with the SDL upload path, not just a screenshot generator. No actual window
pixel/hash comparison was possible here.

Mouse down/motion/up pass through frontend mapping to the shared touch
abstraction. Mouse-up handling can defer release until enough guest frames
have passed. That dependency must be considered when servicing input during
a guest-frozen hold; it has not been validated or changed in O.

Event pumping, guest rounds, and screen presentation occur on the same thread.
The current N hold loop services its control-file channel but does not pump
SDL events or present the actual frontend. After an SDL-enabled runner is
available, a bounded host-only service callback may be needed. This is a
source-supported follow-up requirement, not a runtime-tested deadlock or a
claim that broad scheduler redesign is necessary. No speculative callback
was installed in this blocked task.

## Geometry: source defaults only

For native-width, stacked, default 2x layout, source requests a 512x768 window
with logical 256x384 content: top `(0,0,256,192)`, bottom `(0,192,256,192)`.
An unletterboxed 2x client would map DS `(x,y)` to `(2x,384+2y)`:
choice 3 `(108,616)`, choice 4 `(256,616)`, Continue `(256,716)`.

These are **not measured client coordinates**. Actual client dimensions,
DPI, drawable scaling, focus, HWND, and screen rectangles remain unmeasured.
Resizable/high-DPI and logical-presentation handling must be accounted for
before authoritative OS input. No hit regions were changed.

## Unperformed proof and safety

Actual-window initial/Incorrect/Correct/rules captures, frontend input
provenance, live repaint, frozen CPU/video samples, clean window handoff,
and normal frontend Back remain **unproven**. No OS mouse automation or
SDL-queue injection was performed. No manual user input was used.

No popup, drawing, exercise, original problem answer, guest progression,
ROM patch, generated-C edit, guest-VRAM UI writes, or save-semantics change.
J?N implementation is untouched; prior popup/headless modes remain as before
by code inspection, without a repeated gameplay regression.

## Reproduction and artifacts

ROM-free helper: `tools/task_o/probe_frontend.py`. It refuses any non-NONE
build and any existing output directory: it is a **failure-only prerequisite
probe**, not the future frontend driver.

```powershell
python tools/task_o/probe_frontend.py --out local/task-o/frontend-unavailable-001
```

Use a new directory name on repetition. The helper checks ROM/save identity,
captures stdout/stderr, records the exact launch command, verifies expected
exit/error, and compares the entire save. A different startup result or any
trace/save activity fails validation.

Ignored evidence: `local/task-o/frontend-unavailable-001/`, containing
`prerequisite.json`, `stdout.log`, `stderr.log`, three empty trace files,
and the before/after save copies. None of these artifacts are committed.
Validation: the one actual startup probe and `git diff --check`.

Supported, narrowly justified escalations ran under the existing auto-review
posture; no human approval was required. No approval/relay/full-access changes
and no newly observed infrastructure failure. The old sandbox setup issue
was not retried in this turn.

## Next step, not implemented

Resolve the SDL-enabled Windows build prerequisite and **retry Task O** before
Task P. Then add only the necessary host-only event/repaint service while held,
including pen-release handling independent of guest frame advancement, and
perform the requested real-window 3 -> 4 -> Continue / Back proof. No Task P
implementation or new integration phase began.
