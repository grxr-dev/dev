# Task O retry 002: live Windows frontend during native hold

Date: 2026-10-09. **PASS using the permitted SDL-queue input fallback.**

The real SDL3 Windows game window shows the native question, Incorrect and
Correct while both guest CPUs remain frozen. Actual client pixels were obtained
through Win32 `PrintWindow`, not synthesized from readback. Session-bound mouse
button events enter `SDL_PushEvent` in client coordinates **before** the normal
SDL renderer coordinate conversion and shared `nds_set_touch` path. All six
custom down/up events are consumed; none reaches the guest. Continue releases
input/presentation ownership before the original compiled lifecycle transition
executes once. Rules and normal Back appear in the same HWND. Save is unchanged.

**Physical OS mouse delivery is not proven.** Two guarded SendInput-mode
preflight attempts could not guarantee foreground ownership, even with temporary
foreground-thread input attachment. Neither sent a click. The allowed SDL-queue
fallback was used deliberately, not relabeled as OS input. The Win32 helper's
historical `source=win32_sendinput` label on observation/capture metadata was
overbroad; it did not mean those actions sent input. Source now labels them
`win32_window_api`. The authoritative driver's `input_source=sdl-queue` and
queue/event/touch provenance unambiguously identify the actual input source.

## Recovery and binaries

Project starting HEAD: `c5d07628205a5017551567112adfece545aeda35`.
Branch remains `codex/brainage`. Framework HEAD remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e` with the prior diagnostic integration.
Exact ROM SHA-1 was checked by the driver and runtime:
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.

Restored the untouched Task G checkpoint:
`local/task-g/session-001/04-training-menu/checkpoint.state`, SHA-256
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
AAA, January 2, ordinary Training selection menu, no active exercise.
The opt-in startup loader uses the existing core savestate ROM/build identity
validation after boot and before the frontend starts; it immediately disables
the inherited force-Tier-3 selector before any guest execution. No identity
check is bypassed. Restored menu current/requested are `0x32`, context is `1`.

Full Flash baseline/final SHA-256 (**H0**):
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

Separate SDL runner: `build/task-o-sdl-runner/nds_runner.exe`, adjacent SDL3.dll.
Authoritative and final built executable SHA-256 are identical:
`16723f72e4337d6b37a34a71c788ca69e7f8c128b66e8c425559645e50a1b9c6`.
SDL3.dll SHA-256 remains
`4659d5a1e240e7d58fb92808f84afeb53395818cec62385d4796b72977a7d859`.

Headless executable remains byte-identical, SHA-256
`19ddb95320ccca985b42ead833c5add233a3d315222dff962c21fae1e022d76c`;
its cache is also unchanged, SHA-256
`6dae0ee28634f24cb79412184301d2ab63b12c94a929fed4ec231c39c2593446`.
Minimal headless `--help` returned 0. No generated bank was edited/regenerated.

## Narrow frontend path and implementation

Source locations refer to the installed local runtime after this integration:

| Point | Function/location | Role |
|---|---|---|
| Window setup | `runner/src/frontend.cpp:1756`, `create_presentation` | Real SDL window, stacked 2x logical DS screens, nearest filtering |
| Main loop | `frontend.cpp:2096`, `nds_run_interactive_frontend` | Same host thread pumps input, executes scheduler and presents |
| Coordinate mapping | `frontend.cpp:1581`, `convert_mouse_event_to_logical_coordinates` | SDL_RenderCoordinatesFromWindow before DS mapping |
| Touch mapping | `frontend.cpp:1005`, `set_touch_from_mouse` | Subtract bottom logical origin 192 and clamp to DS coordinates |
| Shared input | `nds_set_touch` | Existing native owner consumes before ADC/EXTKEYIN mutation |
| Presentation | `frontend.cpp:1989`, `present_screens` | Upload textures and SDL_RenderPresent in the real game window |
| Shared bottom source | `frontend.cpp:3920` | Task N's `nds_gpu2d_presented_framebuffer` |
| Held host service | `frontend.cpp:2884` and `4469` | Scoped callback; poll host events and present existing pixels only |
| Test queue boundary | `frontend.cpp:940` | Session-token/next-sequence checked client-coordinate SDL events |

Previously the synchronous native hold blocked the outer event/render loop.
`nds_frontend_service_native_hold()` now invokes one scoped host-only callback
from that hold. It pumps SDL events, routes ordinary mapped mouse events and
uploads/presents raw guest top plus Task N presented bottom. It does not run a
scheduler round, guest CPU, timer, device event, adaptive compositor or debug
command. Native release is immediate, not deferred for two nonexistent guest
frames. The ordinary inactive release behavior is unchanged. Focus loss releases
contact; close/presentation failure cancels the hold with scoped owner cleanup
rather than faking guest continuation. Close during hold was not exercised.

The callback is cleared on frontend scope exit and invoked only by the native
surface hold. Headless has no installed callback. The shared header's feature
guard also permits older J-N installations without this frontend API. Original
popup mode remains the unchanged branch when Task N presentation is disabled.
Existing J/N selectors remain disabled by default; no global plugin system.

New opt-in diagnostics:
- `NDS_TASK_O_START_STATE`: exact-title, validated pre-execution checkpoint load.
- `NDS_TASK_O_FRONTEND_TRACE`: compact event/mapping/ownership provenance.
- `NDS_TASK_O_WINDOW_CONTROL` and `NDS_TASK_O_CONTROL_TOKEN`: optional SDL-queue
  test channel. Fresh token and exact next sequence; stale, duplicate, malformed,
  out-of-window and out-of-order requests do not enqueue an event. No direct
  MiniExercise or `nds_set_touch` call from this channel.

## Actual-window geometry and pixels

Authoritative evidence: `local/task-o/retry-002/sdl-queue-002/`.
PID **126080**, HWND **12128058**, class **SDL_app**, title initially
**ndsrecomp firmware preview**. The same PID/HWND is observed in every capture.
Client **512x768**, DPI **96** (100%), screen client origin **(1024,316)**.
Window bounds **(1016,285)..(1544,1092)**, outer size **528x807**.
Top client rectangle `[0,0)..[512,384)`; bottom `[0,384)..[512,768)`.
DS-to-client mapping: `(2*x, 384+2*y)`; screen adds the measured origin.

PrintWindow with client/full-content flags returned meaningful pixels without
requiring foreground focus. No desktop reconstruction or framebuffer-only
substitute was used. Each custom bottom crop is **exact** 2x nearest expansion;
the analyzer checks every duplicated pixel and row. Reduced RGB SHA-1 equals
the native surface and shared readback hash in each phase:

| Actual client capture | Bottom RGB SHA-1 after exact 2x reduction |
|---|---|
| Initial and later initial | `ecca6be984b92e963cc84fdcbc7014c88fcbb720` |
| Incorrect | `97e88b8c2ce5b958af44c2a3b8ac408d66405289` |
| Correct | `603764477fe3a3089edd806a1a32c81d180b425e` |
| Original rules | `94d67eb1801b7b8d062e8779fc3f29de2ea002d8` |

Actual top crop SHA-256 remains
`36add41a0fd3ed9f2490d7e7e3d0f4645727998fcf8b9be721994ddeac729136`
through all four held captures. Source surface is native 256x192 ARGB8888;
top source remains guest. There is no separate popup. Rules capture exactly
matches contemporaneous guest readback, with the ordinary handwriting-demo
animation/gray More at that sampling point. Prior Task N captured a later
demo frame with More green (`ec242e590e2c1ced765cef2802ab69985959e400`), so
cross-run whole-screen identity is **not** claimed. Text/layout, scene state,
single initialization and Back behavior agree. No-input settling preserves rules
scene and clean pen; original guest advancement resumes normally.

## Authoritative frontend input and freeze

All custom actions use SDL event-queue client coordinates, before normal
conversion, not Task L choose/Continue or Task M raw DS touch controls.
Read-only session-bound sample/capture diagnostics are used while held.
No Graham/manual input was requested or required.

| Action | Client | Screen correspondence (not OS-injected) | Logical frontend | DS down |
|---|---|---|---|---|
| Choice 3 | (108,616) | (1132,932) | (54,308) | (54,116) |
| Choice 4 | (256,616) | (1280,932) | (128,308) | (128,116) |
| Continue | (256,716) | (1280,1032) | (128,358) | (128,166) |
| Original Back | (480,448) | (1504,764) | (240,224) | (240,32) |

Queue control sequences 1/2 select x20, 3/4 choose 3, 5/6 choose 4, 7/8
Continue, 9/10 Back. For each: queue acceptance -> SDL_PollEvent raw client
record -> renderer logical conversion -> `set_touch_from_mouse` ->
`nds_set_touch` -> owner/guest-delivery record. Pen-up uses the original shared
mapper's `(0,0,false)` release; the native contact resolves its stored down
target. This is intentional, not an incorrect DS release coordinate claim.

Choice 3 makes attempt 1 Incorrect; Choice 4 makes attempt 2 Correct with
Continue enabled. All six custom events have `owner=true`, `consumed=true`,
guest delivery count **3 -> 3**. Back has no owner and increases guest deliveries
**3 -> 4 -> 5**, returning current/requested to `0x32` and the visible Training
selection menu. Original exercise is never started or completed.

Compiled interception occurs once at PC `0x0204D790`, opcode `0xE92D4030`,
LR `0x02050268`, current/requested/selected `0x32/0x41/0x11`, menu context 1.
The following remain invariant across every native event/sample:

| Guest measurement | Value |
|---|---|
| ARM9 cycles | 2339189601 |
| System cycles | 1169594800 |
| ARM7 cycles | 1169594755 |
| ARM9 ordinal | 210027404 |
| ARM7 ordinal | 69527056 |
| Guest top RGB SHA-1 | `1ce37a48fb8a74c9e2e9f05158efb24f3db4c85d` |
| Guest raw bottom RGB SHA-1 | `26ddaba91081d36959644f4dbdcb613e56d447b1` |
| Measured guest video SHA-1 | `56506dea804bc3d1cb48b439c4095efca682d709` |

Video measurement remains the prior probe's 675840-byte physical VRAM A-I,
palettes and OAM digest; no broader renderer immutability is claimed. Guest
registers/CPSR and Flash SHA-1 also remain unchanged. Host held presentation
counter grows **6 -> 151** across a three-host-second observation interval,
then to **197** after completion and **208** before release. Thus this is not a
one-frame overlay or guest progression hidden underneath the panel.

## Handoff, saves and bounds

Native audit sequence 21: touch release clean; 22: touch owner removed;
23: presentation owner removed and native surface destroyed;
25: original transition allowed to execute. Guest contact is released,
ADC `(0,4095)`, both owners false, surface digest empty before resume.
No synthetic return, stack change, scene-global forgery or ROM modification.

Original lifecycle executes once. Rules initializer `0x020610B4` executes once
(natural Tier-3 fallback, no forcing); calculation constructor count is zero.
Current/requested/selected become `0x41/0x41/0x11`. The same real window shows
guest rules; no native pixels or stale custom touch remain. During no-input
settling ARM9 cycles advance `2460354480 -> 2517493860`, guest deliveries stay
3, clean pen remains released and scene globals stay unchanged. Back also uses
the ordinary SDL queue/frontend mapping and reaches the visible Training menu.
Close uses the supported `frontend_exit -> SDL_QUIT`; runner exits **0**.

**0 logical save operations, 0 Flash commits, 0 changed bytes** across the
authoritative run. Complete 256 KiB before/after images equal H0 byte-for-byte.
No custom pixels were written into guest VRAM; no generated recomp C edited.

This proves Windows SDL presentation, live host servicing during the synchronous
guest hold, SDL-frontend-coordinate input ownership and clean handoff. It does
not prove physical Win32 mouse delivery, other platforms, real DS hardware,
guest-rendered custom scenes, handwriting, voice, new menu entries or custom
result/save integration. Recommended next smallest Task P: repeat this same
bounded probe through verified physical OS SendInput when foreground targeting
can be guaranteed, rather than advancing to a larger exercise. **Not started.**

## Artifacts and reproduction

ROM-free project changes:
- `tools/task_j/brainage_native_probe.h`: optional frontend service and audit count.
- `tools/task_o/install.py`: pinned, idempotent host-runtime integration.
- `tools/task_o/hold_service.inc`: scoped host service, no guest execution.
- `tools/task_o/event_trace.inc`: raw frontend and mapped touch provenance.
- `tools/task_o/queue_input.inc`: optional session/sequence-bound SDL injection.
- `tools/task_o/window_probe.cpp`: exact-PID/path window identity, geometry,
  PrintWindow/BitBlt capture and guarded SendInput support.
- `tools/task_o/drive_frontend.py`, `tools/task_o/analyze.py`: bounded run and audit.
- This report and historical Task O report link.

Installed ignored runtime files: `runner/src/{frontend.h,frontend.cpp,main.cpp,
debug_server.h,debug_server.cpp,brainage_native_probe.h}`. Existing SDL-only build
is rebuilt; old headless executable is not. No SDK/binary/game captures tracked.

From the prepared checkout/toolchain, with ordinary review:

```powershell
python tools/task_o/install.py --codex-executable C:\Users\rustg\AppData\Local\OpenAI\Codex\bin\9691020b546a15b2\codex.exe
$env:PATH = "$PWD\local\toolchain\w64devkit\bin;$env:PATH"
cmake --build build/task-o-sdl-runner --target nds_runner --parallel 4
g++ -std=c++17 -O2 -Wall -Wextra tools/task_o/window_probe.cpp -o build/task-o-tools/window_probe.exe -luser32 -lgdi32 -static-libgcc -static-libstdc++
python tools/task_o/drive_frontend.py --out local/task-o/retry-002/new-run --input-source sdl-queue
python tools/task_o/analyze.py --out local/task-o/retry-002/new-run
```

Create `build/task-o-tools` if absent. Each evidence directory must be new.
OS input is available as `--input-source win32-sendinput` but intentionally
fails before clicking if exact foreground ownership cannot be verified.

All partial attempts remain local: `run-001`, `run-002` failed before input;
`window-check-001` exposed a driver response-key mismatch before input;
`window-check-002` obtained real PrintWindow pixels and exited cleanly;
`sdl-queue-001` completed interaction/Back but its too-early menu capture was
in the normal fade and failed the capture check. It was not promoted to a full
PASS. `sdl-queue-002` is the complete authoritative run with settled Back and
clean close. No prior Task G-N evidence was changed.

Checks: helper C++ build, Python syntax, exact pixel/input/save audit, final SDL
build, installer idempotence and headless help/hash. Routine escalated operations
were auto-reviewed; no human approval was needed. Built-in apply_patch could not
write initially; the existing reviewed bundled apply_patch path succeeded.
No node/Computer Use helper or relay/approval-policy change was used.
