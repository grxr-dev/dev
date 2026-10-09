# Task Q: continuous freehand through the custom-exercise contract

Date: 2026-10-09. **PASS** on the real SDL3 Windows frontend, using explicitly
classified SDL-queue input. No recognition or Decuma integration is implemented.

## Architecture and selection

Started from Task P commit `e0c95fe472f4645f01c9d908a11e0ec53c1b2389` on
`codex/brainage`. Framework remains pinned at
`3a57236bb23d25dcb4caad7d58d733311062ff5e`.

`bc_host.h` is byte/normalized-text identical to Task P. Lifecycle gating,
compiled/Tier-3 entry, hold loop, frontend host service, touch owner,
presentation owner, cleanup and exactly-once resume are unchanged. The host
contains no canvas, stroke or freehand-specific branches. Existing
`touch(x,y,down)` already supports repeated down updates as motion.

`bc_catalog.h` now has exactly two static descriptors: `arithmetic-2plus2` and
`freehand-canvas`. `NDS_BRAINAGE_CUSTOM_EXERCISE_ID=freehand-canvas` selects the
new implementation when custom activation is enabled. Missing/empty ID retains
the quiz, including legacy activation. Unknown nonempty IDs raise a clear
`unknown Brain Age custom exercise ID: ...` error at catalog resolution, before
instance creation or input/presentation acquisition. No registry UI, dynamic
loading, scene extension or Brain Age menu entry is added.

The only contract addition is optional owned numeric diagnostic metadata on
`ExerciseStatus`. The previous generic status could not describe non-quiz local
metrics. There is no functional touch/event/exit API change and no stroke fields
in lifecycle decisions. The diagnostic adapter serializes metadata; the existing
host naturally caches the final status, so metrics survive instance destruction
without freehand-specific code. Diagnostics are not required to draw or exit.

## Exercise and rendering policy

`tools/brainage_custom/bc_freehand.h` owns:
- Canvas inclusive bounds **x24..232, y32..136**; visible border one pixel outside.
- Continue inclusive bounds **x72..184, y148..184**.
- Fixed **8 stroke descriptors**, **256 total point slots**; no unbounded capture.
- Current contact mode, points, completed strokes, completion/exit permission.
- Two released nonempty strokes enable Continue; no interpretation of shape.

First down inside the canvas starts one stroke and records one point. Subsequent
down updates append changed in-bounds positions to that same stroke. Identical
points are ignored. Motion outside the canvas is ignored, retaining contact;
on re-entry the next point connects to the last accepted in-bounds point. A
contact starting outside the canvas never becomes a stroke. Release closes a
stroke once, does not append `(0,0,false)`, and duplicate release is harmless.
Contacts beginning on Continue are separate from drawing; moving out cancels
that button contact. Premature Continue is rejected on release.

At either storage limit, no new slots are written; excess points/new drawing
contacts are ignored and a diagnostic limit flag is set. Existing active contact
can still release safely. Capacity, outside-contact and duplicate-release cases
were tested locally. The authoritative gesture never reached a limit.

`Surface::line` is a generic deterministic integer Bresenham primitive with
inclusive endpoints and **one-pixel** ink thickness. It rejects a line with any
endpoint outside the 256x192 surface before arithmetic/indexing; it does not clip
invalid endpoints. Freehand coordinates remain inside the canvas. Horizontal,
vertical, rising/falling diagonal, point/endpoints, surface edge and extreme
out-of-bounds arguments passed focused tests. Four missing ROM-free ASCII glyphs
were added; quiz pixel-equivalence tests remain unchanged/passing.

Exercise metadata reports `completed_strokes`, `point_count`, `current_points`,
`active_contact`, `storage_limited`, and deterministic `stroke_hash`. The hash is
a 32-bit FNV-style update over each stored stroke count and its ordered x/y
values; it is only an identity check, not recognition or a normalized format.

## Frontend input extension

The existing optional session-token/next-sequence SDL queue channel keeps old
button syntax and adds kind **2** for held-left-button motion:

`token sequence kind client-x client-y`, where 1=down, 2=motion, 0=up.

Motion without an accepted queued contact, duplicate down, up without contact,
stale tokens/sequences, malformed or out-of-window requests are rejected. This
is a diagnostic SDL event injector, not an exercise/DS-touch shortcut.
`SDL_PushEvent` supplies normal button/motion events before the existing
`SDL_RenderCoordinatesFromWindow` mapping and `set_touch_from_mouse` calls.
The existing held-service mouse-motion branch already routes repeated down
events through `nds_set_touch`; it required **no change**.

Read-only provenance now includes held-left-button frontend motion alongside
buttons. The ordinary touch owner and guest ADC/EXTKEYIN paths are unchanged.
Task Q's installer updates only the owned queue/provenance snippets and exercise
headers; it never rewrites generated banks or scheduler code. Prior numeric
button-only helpers remain supported.

## Recovery and authoritative run

Evidence: `local/task-q/normal-enabled-001/`. One authoritative runtime run.
Restored untouched Task G Training checkpoint
`local/task-g/session-001/04-training-menu/checkpoint.state`, SHA-256
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
AAA, January 2, normal Training menu; inherited force-Tier-3 is disabled by the
existing identity-validated startup loader before guest execution.

Exact ROM SHA-1 verified:
`b8a105bacc3234dede8d4465df0869f2b922a0e2`.
Separate SDL runner SHA-256:
`c47e21fd4e503eaac73700cba8b480a8e5285a077be1c9af59ec7cc8b91331ce`.

Activation uses stable host/presentation selectors, both `1`, plus
`NDS_BRAINAGE_CUSTOM_EXERCISE_ID=freehand-canvas`. The process-local existing
`NDS_SDL_RENDER_DRIVER=software` is retained from Task P for actual-window
capture. It changes only the host SDL presenter, not guest graphics.

PID **123460**, HWND **15076774**, class **SDL_app**, client **512x768**, DPI
**96**, client screen origin **(48,71)**. Top client rect is (0,0)-(512,384);
bottom is (0,384)-(512,768). DS -> client mapping is `(2*x,384+2*y)`.
No popup is created. Every capture uses the same real SDL game window.

The exact compiled ARM9 lifecycle boundary `0x0204D790` is intercepted once with
the unchanged Task P predicate. The factory creates `freehand-canvas` once.
The ordinary x20 selection is not modified and no original exercise is started.

| Gesture | DS positions / action | Result on release |
|---|---|---|
| Stroke 1 | Down (64,48); motion (96,72), (128,96), (160,120), (192,132); up | 1 completed stroke, 5 points, contact false, Continue disabled |
| Premature Continue | Frontend down/up at (128,166) | Rejected; remains 1 stroke/5 points, guest held |
| Stroke 2 | Down (192,48); motion (160,72), (128,96), (96,120), (64,132); up | 2 completed strokes, 10 points, contact false, Continue enabled |
| Final Continue | Frontend down/up at (128,166) | Accepted once on release; common cleanup then original resume |

There are exactly **2 initial drawing downs, 8 held motion updates, 2 drawing
releases**. Each drawing release maps to `(0,0,false)` through the ordinary
frontend path; its raw window release coordinate remains the last point.
Continue contacts are not counted as strokes. All **16** custom touch events
are consumed by the native owner, with **0** guest deliveries. Input provenance
connects queued event, client/logical coordinates, mapped DS touch and exercise
snapshot for every drawing event. No direct Exercise, direct `nds_set_touch`,
raw-DS diagnostic, diagnostic choose/Continue or human input is used.

## Actual pixels and continuous line proof

Actual OS client captures use `PrintWindow`, not reconstructed readback images.
Empty canvas, Stroke 1, Stroke 2, original rules and returned Training captures
were visually inspected. Native/shared readback and actual captured bottom RGB
hashes match exactly at 2x nearest scale for held states and original rules.

| State | Actual-window bottom RGB SHA-1 |
|---|---|
| Empty and later empty | `86345695bfb63a2d9209288bff9fd330a7844b3b` |
| Stroke 1 | `a24db854231fd82b7a12f6f248fbeb42f9a71dd1` |
| Stroke 2 / Continue enabled | `60cbcacc035fb3cedff07e0fdda88998c86064e6` |
| Original rules | `ec242e590e2c1ced765cef2802ab69985959e400` |

The analyzer reads the actual BMP pixels, proving ink RGB **15283f** at these
non-input interpolation points:
- Stroke 1: **(80,60), (112,84), (144,108), (176,126)**.
- Stroke 2: **(176,60), (144,84), (112,108), (80,126)**.

None is a sampled gesture point. This is connected line rendering, not isolated
dots. The native status only counts strokes; it never recognizes an X or labels
the drawing correct. Host-rendered native pixels never enter guest VRAM.

## Freeze, cleanup and save safety

Every captured native audit row preserves the same register/guest invariant:
- Current/requested/selected **0x32/0x41/0x11**.
- ARM9/ARM7 cycles **2510607823 / 1255303911**.
- ARM9/ARM7 instruction ordinals **218639817 / 73832637**.
- Raw guest bottom SHA-1 **ffd9a948f22950f7593b34ad5c0db8f757d17537**.
- VRAM A-I/palettes/OAM aggregate SHA-1 **a13deb62d1ddb9ccb77ed7b3a6d057c7cbb45717**.
- Guest touch delivery count remains **3** throughout native ownership.

Frontend held-present samples advance **8 -> 143 -> ... -> 290** while guest
counters/video remain unchanged. Rendering occurred **13** times through the
host contract; **16** custom touch calls reached the exercise. Final cached
metrics are 2 strokes, 10 points, no active contact/limit, stroke hash
**4165096879**, retained safely after destruction.

Unchanged host cleanup proves contact/guest ADC released, removes touch owner,
removes presentation owner/surface, destroys the instance, verifies guest state,
then returns naturally to the original transition once. Normal rules appear in
the same window with current/requested **0x41**, selected **0x11**, one rules
initializer and zero calculation constructors. The original initializer
naturally uses runtime fallback; the target lifecycle entry is compiled and
force-Tier-3 remains disabled.

No-input settling produces no stale touch or canvas pixels. Original Back uses
the frontend at DS **(240,32)**; its two events are guest-owned and delivered
normally. Training returns with current/requested **0x32**. Original x20 is
neither started nor completed and no guest completion credit is awarded.
The runner exits cleanly, code 0, without forced cleanup.

Complete 256 KiB Flash before/after SHA-256:
`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.
Logical save operations **0**, Flash commits **0**, changed bytes **0**.

## Focused regression and reproduction

Line/freehand capacity, contact, interpolation and selector tests passed.
The existing quiz contract/pixel test still passes. Actual environment tests
verify default/legacy/stable no-ID -> quiz, empty -> quiz, explicit freehand and
clear unknown-ID rejection. No second runtime exercise was performed.

Installer idempotence, Python syntax and diff checks passed. The prior headless
binary/cache remain unchanged at Task P hashes; `--help` returned 0. The SDL
build remains separate. No ROM patch or generated recomp C manual edit occurs.

With the existing local toolchain on PATH:

```powershell
python tools/task_q/install.py --codex-executable <installed-codex.exe>
cmake --build build/task-o-sdl-runner --target nds_runner --parallel 4
g++ -std=c++17 -Wall -Wextra -I tools/brainage_custom tools/task_q/freehand_test.cpp -o build/task-q-tests/freehand_test.exe -static-libgcc -static-libstdc++
python tools/task_q/check_selection.py --binary build/task-q-tests/freehand_test.exe --out local/task-q/selection-check.json
python tools/task_q/drive.py --out local/task-q/new-session
python tools/task_q/analyze.py --out local/task-q/new-session
```

Use a fresh output directory. Saves, savestates, actual game window captures,
readbacks and raw local logs stay ignored. `audit.json` and compact
`stroke-provenance.json` preserve derived evidence locally; only ROM-free
implementation, helpers/tests and this report are committed.

## Limits and recommended Task R

This proves continuous native stylus capture/rendering and reuse of the same
host with a second exercise. It does not prove recognition, Decuma reuse,
production stroke normalization, pressure/tilt, physical SendInput/pen parity,
guest-rendered custom graphics, saves/history, new menu entries or voice.

Recommended next experiment **only**: a bounded map of Brain Age's existing
Decuma input boundary for one original handwriting answer, including stroke
coordinate/contact representation, immediate caller and recognition invocation.
Prefer existing accepted-answer artifacts first. Establish that contract before
attempting any stroke adapter; do not infer recognition compatibility merely
from Task Q's point arrays. **Task R is not implemented or begun.**
