# Task O.5 continuation - isolated SDL3 Windows runner

## Result and boundary

**SDL build/runtime provisioning succeeded.** The separately built runner
starts interactively, exposes a real process-owned game window, presents
ordinary guest frames, and exits cleanly through its existing SDL_QUIT path.
The old headless runner and all measured generated inputs remain unchanged.

**Full OS-window visual confirmation remains unverified.** The supported
Computer Use `node_repl` initialization failed twice with:

```text
trusted Node process exited unexpectedly; kernel reset, rerun your request
```

No security/approval/helper infrastructure was modified to bypass that failure.
The smoke evidence below combines process-owned window metadata, active SDL
presentation counters and visually inspected ordinary guest readback images.
Those images are **not OS-window screenshots**. Do not promote this to the
actual-window custom-surface proof requested by Task O, or claim the physical
window's pixel content was captured. O.5 is a build/runtime PASS with a visual
verification limitation, not an unqualified full-visual PASS.

No Task O quiz/input/hold-service implementation, Task O retry, or Task P began.

## Recovery, dependency and backend

Project starting commit: `26c182b2f07f4d64d52c359331f509cd7cdcf685`.
Pinned framework: `3a57236bb23d25dcb4caad7d58d733311062ff5e`, retaining the
existing J-N integration. The earlier missing-SDK report and its inventories
remain untouched in `docs/BrainAge_TaskO5_SDLProvisioning.md` and
`local/task-o5/dependency-search-001/`.

The dependency was now supplied locally:

```text
local/toolchain/SDL3-devel-3.4.18-mingw.zip
SHA-256 cd98158c8d025a816f430a600b4e9526524e6219ee884ec72bd498b80fd3bf58
```

It matches the previously verified official release asset identity. No download
was needed or performed in this continuation. It was extracted only under
ignored `local/toolchain/SDL3-3.4.18/`, after checking archive paths stay inside
that root. The x64 package contains headers, `libSDL3.dll.a`, `SDL3.dll`, and
`lib/cmake/SDL3/SDL3Config.cmake`; these were checked before configuring.

Both SDL backends remain supported by the actual pinned CMake:

- SDL3: `NDS_SDL_BACKEND=SDL3`, external CONFIG discovery, target `SDL3::SDL3`.
- SDL2: `NDS_SDL_BACKEND=SDL2`, external CONFIG discovery, target `SDL2::SDL2`.
- Headless: `NDS_SDL_BACKEND=NONE`, unchanged and still independent.

No explicit SDL version constraint is imposed by those find-package calls.
SDL3 is the current runner default/preferred backend, chosen without framework
changes. Toolchain is existing w64devkit GCC 16.2.0 / x86_64-w64-mingw32,
CMake 4.4.3 and Ninja. The supplied SDK compiled/linked successfully with it.

## Separate build and exact reproduction

ROM-free helper: `tools/task_o5/build_sdl_runner.py`. Run from `dev`:

```powershell
python tools/task_o5/build_sdl_runner.py --out local/task-o5/build-001
```

Use a new evidence-directory name when repeating. It verifies/extracts the
local pinned archive, writes the full argv/logs, configures and builds only the
separate `build/task-o-sdl-runner` target, then copies its matching x64 SDL DLL
adjacent to the executable. It never downloads a dependency. Compiler PATH
augmentation belongs only to its subprocess environment.

Exact configure argv, expressed with repository-relative paths below (the
helper passes absolute paths), uses the architecture-specific config directly:

```powershell
$repo = (Get-Location).Path
$bin = "$repo/local/toolchain/w64devkit/bin"
$prefix = "$repo/local/toolchain/SDL3-3.4.18/x86_64-w64-mingw32"
$env:PATH = "$bin;$env:PATH"
& "$bin/cmake.exe" -S "$repo/local/ndsrecomp/runner" -B "$repo/build/task-o-sdl-runner" -G Ninja `
    "-DCMAKE_MAKE_PROGRAM=$bin/ninja.exe" `
    "-DCMAKE_C_COMPILER=$bin/gcc.exe" "-DCMAKE_CXX_COMPILER=$bin/g++.exe" `
    -DCMAKE_BUILD_TYPE=Release -DNDS_SDL_BACKEND=SDL3 `
    "-DSDL3_DIR=$prefix/lib/cmake/SDL3" "-DCMAKE_PREFIX_PATH=$prefix" `
    -DNDS_ENABLE_COMPUTE_RENDERER=OFF -DNDS_BOOTSTRAP_FIRMWARE=ON `
    "-DNDS_GENERATED_DIR=$repo/generated/public" `
    "-DNDS_TITLE_BANK_DIR=$repo/generated/brainage" `
    -DNDS_TITLE_ROM_SHA1=b8a105bacc3234dede8d4465df0869f2b922a0e2 `
    "-DNDS_RECOMP_UI_ROOT=$repo/local/recomp-ui" `
    "-DNDSRECOMP_TOMLPP_HEADER=$repo/local/ndsrecomp/recompiler/third_party/toml.hpp" `
    -DNDSRECOMP_COMPILER_CACHE=OFF -DNDSRECOMP_COMPILE_JOBS=4 -DNDSRECOMP_LINK_JOBS=1
& "$bin/cmake.exe" --build "$repo/build/task-o-sdl-runner" --target nds_runner --parallel 4
```

Configure exit **0**; build exit **0**. Existing compiler warnings (generated
unused labels, runtime indentation/initializer/extern warnings) were preserved,
not manually silenced. No unrelated warning repair or optimization.

Built runner SHA-256:
`e1a2e233e32b677cb25e566d47cbdb3d879958d6172557023de25261c704429f`.
Adjacent SDL3.dll SHA-256:
`4659d5a1e240e7d58fb92808f84afeb53395818cec62385d4796b72977a7d859`.

`objdump -p` inspected imports of both binaries: runner needs SDL3.dll plus
Windows system DLLs; SDL3.dll also imports Windows system DLLs. No additional
GCC runtime DLL was listed. No permanent machine PATH, global installer or
package-manager change. Software guest rendering is retained by keeping the
baseline compute-renderer option OFF.

Build evidence: `local/task-o5/build-001/commands.json`, `configure.log`,
`build.log`, `build-result.json`, `protected-before.json`, `protected-after.json`.

## One bounded interactive smoke

ROM-free helper: `tools/task_o5/smoke_frontend.py`:

```powershell
python tools/task_o5/smoke_frontend.py --out local/task-o5/smoke-001 --seconds 20
```

It fresh-launches the SDL runner normally from reset, no checkpoint restoration
and no forced Tier-3, using direct boot / FreeBIOS / generated firmware and
the unchanged existing config. It verifies exact ROM SHA-1
`b8a105bacc3234dede8d4465df0869f2b922a0e2` first and uses an isolated copy of
the known Task G save. Custom J and N selectors are explicitly **0**; inherited
task/frontend diagnostic selectors are removed. January-2 RTC control is
retained. Networking is disabled. No guest key/touch input is sent.

Observed PID **30040**, executable path exactly
`build/task-o-sdl-runner/nds_runner.exe`, process-owned main-window handle
**19334582**, responding **true** in both samples. Titles:

- Initial: `ndsrecomp firmware preview - 111. FPS`.
- Settled: `ndsrecomp firmware preview - 39.3 FPS - Gov S2`.

These came from standard process/window metadata, not reconstructed window
handles or a separate fake UI. Actual client dimensions/class/DPI were not
measured; the source default remains stacked 2x, requested 512x768.

| Observation | Host seconds | Active | Real presented frames |
| --- | --- | --- | --- |
| Initial | 2.484 | 1 | 115 |
| Settled | 20.478 | 1 | 853 |
| Normal close log | about 20 | frontend ended | 875 total |

The SDL log identifies its normal stacked/software presentation path; there is
no missing-backend error. Presentation continued while normal guest execution
advanced (this is **not** a custom/frozen hold test). Forced selector reports
false, forced misses 0. The closing log confirms 0 key presses and 0 touch
presses. The active window reached ordinary Brain Age output without input.

Visually inspected **shared guest readback**, 256x192 per physical screen:

- `settled-A.png`: Brain Age title / Dr Kawashima image.
- `settled-B.png`: ordinary menu, Quick Play / Daily Training / Sudoku / Download.

Settled RGB24 SHA-256:

```text
A a0f298c8bc7c58a283fdf76d13ed995a5d331a9e34e4bc6ece286fb6ea5f239d
B 2d3d1579d272095478589f59d21af36a1fb55e8e56f564fd8adbf8ff26037a38
```

This establishes valid ordinary source pixels accompanying SDL presents, not
an OS-window pixel/hash comparison. Actual-window visual capture could not
be performed because the supported Computer Use process failed at initialization.
No custom Win32 capture/input workaround or helper-infrastructure change was
introduced to sidestep that failure.

Normal deterministic close used only the existing request:

```json
{"cmd":"frontend_exit"}
```

Response `{"requested":1}`. Source route is
`nds_frontend_request_exit` -> `SDL_QUIT` -> normal frontend loop exit/cleanup.
Process exited **0**, with no forced termination and no Graham input. The
runner is no longer running. This is normal SDL close signaling, not a quiz
action, OS mouse injection, or guest-logic skip.

Non-blocking observed warning: final log reports 714 audio underruns and
ordinary perf-governor stage 2. No audio/performance PASS is claimed and no
performance matrix or tuning was attempted in this provisioning task.

Smoke evidence: `local/task-o5/smoke-001/`, including exact launch/session,
`smoke-result.json`, stdout/stderr, before/after saves, empty trace files and
four normal readback PNGs. Game-derived artifacts stay ignored/local.

## Save, source and headless preservation

Smoke before/after full 256 KiB Flash SHA-256:

```text
a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb
```

Changed bytes **0**; logical request trace lines **0**; Flash commits **0**.
No profile selection or exercise began; no custom panel or custom input ran.

Build helper verified **24 protected files** unchanged: old headless executable,
its CMake cache, and generated/public + generated/brainage C/header inputs.
No generated recomp C regeneration/manual edit, ROM patch, guest-VRAM custom
painting, save semantics, or J-N touch/presentation/hold code modification.

Post-build headless check: `nds_runner.exe --help` returned **0**, printed usage,
with no ROM/save supplied. Evidence `local/task-o5/headless-check-002/`.
Old runner SHA-256 remains
`19ddb95320ccca985b42ead833c5add233a3d315222dff962c21fae1e022d76c`;
cache remains
`6dae0ee28634f24cb79412184301d2ab63b12c94a929fed4ec231c39c2593446`, backend NONE.

Validation: one configure/build, one bounded normal startup/readback/close smoke,
one headless help check, Python compilation and whitespace checks. No full
J-N regression or additional gameplay. SDK ZIP/extracted files/DLLs/executables,
saves, readbacks and logs are ignored; only this report and the two ROM-free
helpers are committed.

## Execution posture and remaining blocker

Supported narrow escalations worked under the established auto-review posture;
no human approval required. No network acquisition, full-access change, sandbox
weakening or relay/approval edits. The actual new infrastructure issue is the
Computer Use trusted Node process exiting during both initialization attempts.

The missing-SDL blocker is resolved: an isolated functioning SDL3 executable
is available for a future Task O retry. Before claiming O.5's full OS-visual
confirmation or performing Task O's actual-window proof, repair/restore the
supported window-observation path outside this task. The SDL build itself does
not require further provisioning. Task O hold-service/input work remains
unimplemented. Stop here; no Task O retry or Task P.
