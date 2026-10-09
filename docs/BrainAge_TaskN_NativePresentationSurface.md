# Brain Age Task N: removable DS-sized native presentation surface

Date: 2026-10-09. **PASS for the runner's shared CPU presentation/readback path.**
A true host-owned 256x192 bottom surface shows the existing quiz, accepts
ordinary DS-coordinate taps **3 -> 4 -> Continue**, and changes visibly from
question to Incorrect to Correct. Both guest CPUs and the measured guest
video remain frozen. Input/presentation ownership is removed and the surface
destroyed before the untouched compiled lifecycle transition resumes once.
Original rules, no-input settling and Back match prior evidence; zero saves.

This is **runner presentation-layer output**, not a guest framebuffer/VRAM
write or a custom guest scene. The authoritative run is headless, using the
normal framebuffer response/readback implementation. No Win32 popup is created
or required. An actual SDL frontend while held and other physical/platform
presentation routes are not claimed as tested.

## Recovery and identity

Existing checkout `dev`, branch `codex/brainage`, started at Task M
`2425bc78fb1b841e331a7c4ff0971ebc64fe65fb`. Framework HEAD remains
`3a57236bb23d25dcb4caad7d58d733311062ff5e`, with the established local diagnostic
integration. Exact ROM SHA-1 was independently verified and checked by the
launcher/runtime: `b8a105bacc3234dede8d4465df0869f2b922a0e2`.

Unchanged source state:
`local/task-g/session-001/04-training-menu/checkpoint.state`, SHA-256
`1f792688cf30f9dffb0433fe33cf28b68d63fb68c4b1aecde0b5da65747e6e36`.
AAA, January 2, 2024, 12:00:34 guest RTC, ordinary Training menu.
Starting/final full Flash SHA-256, **H0**:

`a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb`.

The launcher omits `--force-tier3` and disables the inherited saved selector
before execution. Its miss counter stays at the inherited 113582860. The target
entry is observed as compiled; later rules initialization naturally uses
Tier-3 in the unchanged bank inventory. No coverage optimization or bank edit.
The K integrity manifest is copied to `local/task-n/reference-integrity.json`
and verified. M phase contexts/images are also compared without modifying them.

## Existing presentation path

The software renderer maintains physical LCD front/back buffers in `gpu2d.cpp`.
`nds_gpu2d_framebuffer(screen)` drains outstanding presentation jobs and returns
the **raw guest** front buffer: 256x192 packed 32-bit ARGB pixels, screen 0 top,
screen 1 bottom. Adaptive readback can instead provide a host-widened surface.
Raw rendering access is left unchanged, including internal adaptive inputs.

The debug `framebuffer` command, used by Task G/M `capture.py`, extracts these
pixels and serializes RGB24 into `{w,h,rgb}`. Its historic A/B request names
select physical LCD 0/1 here, not an invariant hardware engine mapping.
The SDL frontend obtains native/adaptive CPU pixel pointers before texture
upload and presentation. These are the two narrow consumers reconciled here;
no broad renderer refactoring or direct-GPU presentation claim.

Readback and mutation run on the owning emulation/frontend thread. Headless
`run_cycles` is synchronously blocked inside the native hold, so another normal
TCP capture request cannot execute there. Task N's sequenced read-only capture
adapter invokes the **same exported normal framebuffer-response function** on
the held thread. This is not an independent screenshot generator: both TCP
`framebuffer` and the adapter pass through identical extraction/serialization
and the same optional owner. Existing PNG tooling encodes that returned RGB.

## Small presentation owner

`tools/task_n/presentation.patch` provides:

- `gpu2d.h/.cpp`: optional bottom presentation pointer,
  `nds_gpu2d_set_bottom_presentation`, owner observation and
  `nds_gpu2d_presented_framebuffer(screen,width,adaptive)`.
- `frontend.cpp`: native and adaptive bottom extraction use the new common
  wrapper; all existing top/direct-presentation logic remains unchanged.
- `debug_server.h/.cpp`: the existing framebuffer extraction is factored into
  `debug_framebuffer_response`, used by both the normal command and held capture.
  Responses add source/owner metadata; pixel serialization is unchanged.

The wrapper returns the owner surface at width 256 for bottom when active,
otherwise exactly the original native/adaptive getter. Top always remains
guest output. No replacement of raw renderer buffers, guest memory mapping,
OAM/palette/VRAM writes, scene table changes or generated C edits. The owner
is one scoped pointer on the existing owning thread, not a plugin registry;
its lifetime is controlled by the native state and is not serialized.

`tools/task_n/native_surface.h` owns exactly 49152 `uint32_t` pixels, 196608
bytes, in the runner's packed ARGB8888 format (BGRA byte order on this host).
A small independently specified 5x7 bitmap glyph set and rectangle/text
functions paint the host MiniExercise state. No game fonts or assets.
The readback RGB24 representation is 147456 bytes. Surface geometry and text
coverage are checked by `tools/task_n/surface_test.cpp`.

The shared probe adds an opt-in popup-free `show_surface` branch, reusing M's
touch owner and the existing validator/control ordering. Its host-only polling
loop handles explicit controls without scheduler calls, CPU execution or
guest clocks. It does not create a Win32 window; no native-popup capture files
exist in the authoritative directory. Repaints happen only after accepted
answers, directly from the same host state. No automatic answer or Continue.

## Activation and old-mode preservation

Both selectors are required:

```text
NDS_TASK_J_CUSTOM_EXERCISE_PROBE=1
NDS_TASK_N_DS_PRESENTATION=1
```

Task N is disabled by default. With its selector absent/0, the prior separate
host panel and M touch behavior remain available. The old polling body is
shared, not replaced; legacy choices/Continue, session checks and UI callbacks
retain their semantics. With no owner installed, readback/frontend pixels
are unchanged. The launcher explicitly sets the presentation selector to 0
unless `--ds-presentation` is requested, avoiding inherited-environment surprises.

Implementation sources changed:

- `tools/task_j/brainage_native_probe.h`: owned surface, popup-free hold,
  shared polling/touch processing, read-only capture, graphics hashes, cleanup.
- `tools/task_j/{control.py,context.py}`: isolated Task N root permissions.
- `tools/task_k/{install.py,launch.py}`: owned header/patch installation and
  explicit `--ds-presentation` launch selector.
- `tools/task_n/{presentation.patch,native_surface.h,surface_test.cpp,drive.py,analyze.py}`.
- This report.

Installed additions are under ignored `local/ndsrecomp/runner/src/`:
`gpu2d.h`, `gpu2d.cpp`, `frontend.cpp`, `debug_server.h`, `debug_server.cpp`,
`brainage_native_probe.h`, `native_surface.h`. Only the runner was rebuilt.

## Geometry and authoritative interaction

Visible rectangles preserve M's inclusive hit regions exactly:

| Control | X | Y | Tap |
| --- | --- | --- | --- |
| 3 | 24..84 | 96..136 | (54,116) |
| 4 | 98..158 | 96..136 | (128,116) |
| 5 | 172..232 | 96..136 | not tested in N |
| Continue | 72..184 | 148..184 | (128,166) |

One-pixel borders/text insets do not change input rectangles. Readback stays
256x192 without rotation/rescaling, aligned 1:1 to the DS input coordinates.
Normal original-game book-view captures may be rotated by the existing tools;
the custom proof images intentionally use the raw coordinate-aligned readback.

Final authoritative root: **`local/task-n/normal-enabled-002/`**, port 19874,
runner PID 84936. The paused process was identity-verified and stopped after
the audit. `normal-enabled-001/` is preserved separately: its initial UI
inspection exposed a missing H glyph. The glyph was corrected, a font-coverage
test added, and the same bounded proof recaptured. No old image/evidence edited.

The original menu tap is (166,75). Exact compiled gate remains:

```text
ARM9 ARM; PC 0204D790; opcode E92D4030; LR 02050268; R0=41
current 020DA464=32; requested 020DA3EC=41
selected 020DA3F0=11; Training context 020DA420=1
```

| Control sequence | Input | State |
| --- | --- | --- |
| 1 | read-only capture initial | question, zero attempts |
| 2/3 | ordinary down/up (54,116) | attempt 1: Incorrect |
| 4 | read-only capture incorrect | Incorrect image |
| 5/6 | ordinary down/up (128,116) | attempt 2: Correct/completed |
| 7 | read-only capture correct | Correct, Continue enabled |
| 8 | read-only held sample | guest still frozen after completion |
| 9/10 | ordinary down/up (128,166) | one Continue accepted on up |

Every answer/Continue comes through the common `nds_set_touch` path. No
answer-specific diagnostic choose/continue and no manual UI input. Six events
are owned/consumed with zero guest deliveries. The same session/strict sequence
checks and atomic publication from M prevent replay/stale controls. Capture
accepts only three fixed labels; existing captures are not overwritten.

## Presentation and video evidence

All hashes below are SHA-1 of **row-major RGB24**, with alpha excluded, so the
native surface and normal serialized capture are directly comparable:

| Phase | Native bottom | Captured bottom |
| --- | --- | --- |
| initial | ecca6be984b92e963cc84fdcbc7014c88fcbb720 | same |
| incorrect | 97e88b8c2ce5b958af44c2a3b8ac408d66405289 | same |
| correct | 603764477fe3a3089edd806a1a32c81d180b425e | same |

These three actual normal-readback PNGs were visually inspected: readable
question/choices, red Incorrect, green Correct and enabled Continue. Top
readback remains guest, hash `1ce37a48fb8a74c9e2e9f05158efb24f3db4c85d`.
All raw guest bottom buffers remain
`ffd9a948f22950f7593b34ad5c0db8f757d17537`, distinct from the custom surfaces.

Guest video isolation also hashes physical regions in this fixed order:
VRAM A..I, palette A, palette B, OAM. Concatenation is **675840 bytes** (660 KiB),
SHA-1 `c9599e3d43e4cb3a8d2b864c33b2ab92f3240d64` throughout all 23 runtime
rows. This uses existing read-only/fenced region access, not unrelated RAM.
Raw top/bottom source hashes and measured physical graphics memory stay
identical across every repaint. Full GPU-register/internal-cache immutability
is not claimed beyond these observations and the explicit no-write source path.

Both guest CPUs remain frozen for **6.0312638 host seconds** from initial capture
to post-completion sample. Across all 23 events:

- ARM9 cycles 2320143205; ARM7 scheduler cycles 1160071557.
- ARM9/ARM7 instruction ordinals 209008089 / 69059507.
- Current/requested/selected scenes 0x32 / 0x41 / 0x11.
- Original register/CPSR context, Flash digest and nonterminal state unchanged.
- Guest pen released, ADC X/Y 0/4095; guest touch deliveries remain 2,
  representing only the original menu-selection down/up.
- Only the held lifecycle entry observed before Continue; no rules initializer.

## Clean handoff and original return

Runtime event order after final up is explicit:

```text
18 Continue accepted
19 native and guest touch verified released
20 touch owner removed
21 presentation owner removed; native surface destroyed
22 normal readback capture of restored underlying guest screens
23 original transition resumes naturally
```

The handoff capture's bottom source is guest and RGB hash exactly equals the
original frozen raw guest bottom; native hash is now empty. This proves visual
removal **before guest execution**, not merely after rules overwrite the pixels.
Scoped cleanup also removes both owners on exceptional exits.

At the first stable original rules screen, current=requested=0x41, selected=0x11,
menu context=1, rules object=0x020E9A00, calculation object=null. Complete context,
both CPU/I/O/dispatch views and both screen images match M's validated rules
exactly. One rules initializer, zero calculation constructors. No fake PC/LR/
scene writes, skipped lifecycle body, duplicate init or reconstructed return.

30000000 requested ARM9 cycles of no-input settling retain the rules, guest
presentation and clean contact; no native pixels or stale touch action.
Original Back at (240,32), settled 150000000 cycles, restores Training with
current=requested=0x32. Both owners remain absent; guest touch count becomes 4
only from normal Back. All phase contexts/images, including this settle and
Back, match M. No Start, original problem answer, exercise or completion credit.

Across every phase: **0 logical save requests, 0 Flash commits, 0 accepted
bytes, 0 changed bytes**, full Flash H0 before/after. Independent old-byte
replay matches live and disk snapshots. No save semantics or profile data changed.

## Reproduction and local artifacts

With the existing pinned runtime/build and untouched G source state:

```powershell
python tools/task_k/install.py --codex-executable <bundled-codex.exe>
g++ -std=c++17 -Wall -Wextra -I tools/task_n -I tools/task_l -I tools/task_m tools/task_n/surface_test.cpp -o local/task-n/surface_test.exe
local/task-n/surface_test.exe
cmake --build build/task-a-runner --target nds_runner --parallel 2
python tools/task_k/launch.py --out local/task-n/<fresh-run> --port 19874 --enabled --ds-presentation
python tools/task_g/capture.py --out local/task-n/<fresh-run> --label 00-menu --cycles 0
python tools/task_j/context.py --out local/task-n/<fresh-run> --name menu
```

Run selection capture and the touch/readback driver concurrently:

```powershell
python tools/task_g/capture.py --out local/task-n/<fresh-run> --label 01-select-x20 --tap 166 75 --cycles 150000000
python tools/task_n/drive.py --out local/task-n/<fresh-run>
```

Then capture rules, no-input settling and original Back:

```powershell
python tools/task_j/context.py --out local/task-n/<fresh-run> --name rules
python tools/task_g/capture.py --out local/task-n/<fresh-run> --label 02-rules-no-input --cycles 30000000
python tools/task_j/context.py --out local/task-n/<fresh-run> --name rules-settled
python tools/task_g/capture.py --out local/task-n/<fresh-run> --label 03-normal-back --tap 240 32 --cycles 150000000
python tools/task_j/context.py --out local/task-n/<fresh-run> --name returned-menu
python tools/task_n/analyze.py --out local/task-n/<fresh-run>
```

Analyzer requires `local/task-n/reference-integrity.json`, copied from M's
unchanged K/source manifest. It checks exact event ordering, source identities,
all four readbacks, phase hashes, guest graphics/CPU invariants, contact,
normal M equivalence, Back and every full-save snapshot.
Evidence: `native-probe.jsonl`, `surface-{initial,incorrect,correct,handoff}-{A,B}.json`,
three pairs of normal-readback PNGs, `interaction-proof.json`, `touch-inputs.json`,
context files, four phase directories and **`audit.json`**. Hand-off JSON is
preserved directly from normal readback without a separate generated proof image.

Build: `build/task-a-runner/nds_runner.exe`; logs under `local/task-n/`
including `build-authoritative.log`. Surface tests, Python compilation,
installation idempotence and whitespace checks pass. Existing framework
warnings were not fixed. A later indentation-only cleanup was rebuilt without
another gameplay run. Both local N runners were safely stopped; no exercise
or broad validation matrix was performed.

All ROM/save/state/game-pixel outputs remain ignored under `local/`. Only
ROM-free source, patch/support, analyzers and this report are committed.

## Execution posture, limits and next task

Initial normal sandbox read failed before execution:
`Failed to create unified exec process: helper_unknown_error: setup refresh had errors`.
Supported narrowly justified escalations worked under auto-review, with no
human approval required. No policy/full-access/relay changes.

**Proven:** removable 256x192 runner readback surface, coordinate-aligned touch,
distinct visual state updates, immutable measured guest video while held,
pre-resume destruction/removal, exact original rules/Back and unchanged saves.

**Not proven:** guest-rendered content, custom pixels in emulated VRAM, actual
physical frontend refresh/input while synchronously held across platforms,
Decuma or arbitrary strokes, guest scoring/history/save integration, new menu
entries/guest scenes or voice. The SDL extraction integration is source-level;
the authoritative visual proof is the shared headless capture/readback route.

Recommended Task O only: one Windows frontend proof that refreshes this same
surface and services an ordinary window-derived tap while held, then returns
to original rules/Back without guest advancement or saves. Keep this same tiny
quiz, no scoring/handwriting/new scene, and do not broaden to multiple platforms.
Not implemented. Task N stops here.
