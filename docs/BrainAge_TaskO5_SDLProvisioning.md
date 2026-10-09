# Task O.5 - SDL-enabled Windows runner prerequisite

## Result: blocked on a missing development package

No usable local SDL2 or SDL3 **development SDK** was found in the bounded
search. Per the task's explicit missing-SDK stop rule, no SDK was downloaded,
no separate runner was configured/built, and no interactive smoke test was
attempted. Task O was not retried. This is not evidence that an SDL build would
fail once its development dependency is supplied.

Project starting commit: `209cb3f689c67f8c3273cbbd8c8cfaf3bf22b4cb`.
Framework remains `3a57236bb23d25dcb4caad7d58d733311062ff5e`, with the existing
J-N diagnostic integrations untouched.

## Pinned build contract

Inspected `local/ndsrecomp/runner/CMakeLists.txt:29` and `:741`:

| Backend | Configure option | Discovery | Required imported target |
| --- | --- | --- | --- |
| Preferred/default | `-DNDS_SDL_BACKEND=SDL3` | `find_package(SDL3 CONFIG REQUIRED)` | `SDL3::SDL3` |
| Compatibility | `-DNDS_SDL_BACKEND=SDL2` | `find_package(SDL2 CONFIG REQUIRED)` | `SDL2::SDL2` |
| Existing headless | `-DNDS_SDL_BACKEND=NONE` | No SDL package | None |

There is **no SDL version argument/constraint in these calls**. SDL is externally
package-discovered, not vendored or automatically fetched by the runner.
`local/ndsrecomp/docs/sdl3-default.md` confirms SDL3 is the preferred frontend;
SDL2 is not selected merely because unrelated applications have SDL2 DLLs.

Chosen backend: **SDL3**, keeping `NDS_ENABLE_COMPUTE_RENDERER=OFF` as in the
headless baseline. Only presentation/input/audio SDL support would change;
the guest software renderer, generated banks, bootstrap configuration and
title integrations stay the same. No new compiler, package manager, SDL_image,
SDL_ttf, or SDL_mixer is required by the inspected runner build.

Prepared toolchain: `local/toolchain/w64devkit/bin`, GCC **16.2.0**, target
**x86_64-w64-mingw32**, CMake **4.4.3**, existing Ninja. Choose the **MinGW
x64 development package**, not a runtime-only ZIP or a Visual C++ SDK. This
matches the compiler/import-library family; actual link/runtime compatibility
remains to be checked after provisioning.

## Bounded local dependency search

Evidence: `local/task-o5/dependency-search-001/search.json`. The inventory
records each root, depth/entry bound, matches, errors and truncation explicitly.
Each root was capped at 20000 entries; depths were 1-8 depending on purpose.
No symlinks were followed; `.git`, `node_modules`, and `__pycache__` were skipped.

Searched:

- Prepared toolchain, recomp-ui, framework external/vendor trees, existing builds,
  and the small sibling `Muse/NDS` directory.
- Downloads/Desktop (bounded), user `.cache`, NuGet caches, Conan/vcpkg/Scoop
  locations, Local Package Cache/cache/Temp.
- Common SDL2/SDL3, MSYS2 MinGW/UCRT include/CMake/bin and pacman archive paths.
- Environment hints for SDL, vcpkg, Conan, CMake and MSYS; no relevant hints found.

Found unrelated BizHawk **SDL2.dll/SDL.dll runtime files** in Downloads/Desktop.
No associated SDL headers, MinGW import library or CMake development config
was found. These DLLs alone cannot satisfy `find_package(... CONFIG REQUIRED)`.
Toolchain matches were generic CMake FindSDL modules, Windows `rasdlg` material,
editor syntax files and NSIS download plugins, not SDL SDKs. Recomp-ui contains
SDL adapters/ImGui backend sources but not SDL itself.

Downloads and Temp reached their entry caps; Temp also had inaccessible
directories. A subsequent shallow Downloads archive scan and top-level Temp
scan found no SDL/vcpkg/Conan archive. This does **not** prove absence everywhere
on disk; it establishes no usable SDK in the inspected prepared/common locations.
No permission restrictions were relaxed to inspect inaccessible directories.

## Exact dependency to supply

Suggested concrete artifact: **`SDL3-devel-3.4.18-mingw.zip`**, from the
[official SDL 3.4.18 release assets](https://github.com/libsdl-org/SDL/releases/expanded_assets/release-3.4.18).
This version is a reproducible provisioning choice, **not** a minimum imposed
by ndsrecomp. No claim of a validated runner build with this version is made.

Official published archive SHA-256:

```text
cd98158c8d025a816f430a600b4e9526524e6219ee884ec72bd498b80fd3bf58
```

Smallest Graham action: download that one official MinGW development ZIP to:

```text
C:\Users\rustg\Documents\Codex\Muse\dev\local\toolchain\SDL3-devel-3.4.18-mingw.zip
```

No global installation or host PATH change is needed. Codex can subsequently
verify/extract it locally. Expected extracted root is
`local/toolchain/SDL3-3.4.18/`, containing `cmake/` plus the
`x86_64-w64-mingw32/` headers/libraries/bin subtree. That distribution layout
and architecture-specific DLL handling are described in the
[official MinGW instructions](https://wiki.libsdl.org/SDL3/INTRO-mingw).
Required material includes SDL3 headers, MinGW import library, CMake config/
target files, and the matching x64 `SDL3.dll` from the same package.

## Exact follow-up commands (NOT executed)

Run from the existing `dev` checkout. Verify identity and actual extracted
config/header/import-library paths before configuring. These commands describe
the next O.5 attempt, not a successful configure/build in this task.

```powershell
$ErrorActionPreference = 'Stop'
$repo = (Get-Location).Path
$bin = (Resolve-Path local/toolchain/w64devkit/bin).Path
$archive = Join-Path $repo 'local/toolchain/SDL3-devel-3.4.18-mingw.zip'
$expected = 'cd98158c8d025a816f430a600b4e9526524e6219ee884ec72bd498b80fd3bf58'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'SDL archive hash mismatch'
}
$sdk = Join-Path $repo 'local/toolchain/SDL3-3.4.18'
if (Test-Path -LiteralPath $sdk) { throw 'Preserve existing SDK; inspect before extracting' }
Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $repo 'local/toolchain')
if (!(Test-Path -LiteralPath "$sdk/cmake") -or
    !(Test-Path -LiteralPath "$sdk/x86_64-w64-mingw32/include/SDL3/SDL.h") -or
    !(Test-Path -LiteralPath "$sdk/x86_64-w64-mingw32/lib/libSDL3.dll.a") -or
    !(Test-Path -LiteralPath "$sdk/x86_64-w64-mingw32/bin/SDL3.dll")) {
    throw 'Unexpected SDL development-package layout; inspect rather than guess'
}
$env:PATH = "$bin;$env:PATH"
& "$bin/cmake.exe" -S local/ndsrecomp/runner -B build/task-o-sdl-runner -G Ninja `
    "-DCMAKE_MAKE_PROGRAM=$bin/ninja.exe" `
    "-DCMAKE_C_COMPILER=$bin/gcc.exe" "-DCMAKE_CXX_COMPILER=$bin/g++.exe" `
    -DCMAKE_BUILD_TYPE=Release -DNDS_SDL_BACKEND=SDL3 `
    "-DSDL3_DIR=$sdk/cmake" "-DCMAKE_PREFIX_PATH=$sdk;$sdk/x86_64-w64-mingw32" `
    -DNDS_ENABLE_COMPUTE_RENDERER=OFF -DNDS_BOOTSTRAP_FIRMWARE=ON `
    "-DNDS_GENERATED_DIR=$repo/generated/public" `
    "-DNDS_TITLE_BANK_DIR=$repo/generated/brainage" `
    -DNDS_TITLE_ROM_SHA1=b8a105bacc3234dede8d4465df0869f2b922a0e2 `
    "-DNDS_RECOMP_UI_ROOT=$repo/local/recomp-ui" `
    "-DNDSRECOMP_TOMLPP_HEADER=$repo/local/ndsrecomp/recompiler/third_party/toml.hpp" `
    -DNDSRECOMP_COMPILER_CACHE=OFF -DNDSRECOMP_COMPILE_JOBS=4 -DNDSRECOMP_LINK_JOBS=1
if ($LASTEXITCODE -ne 0) { throw 'SDL runner configure failed' }
& "$bin/cmake.exe" --build build/task-o-sdl-runner --target nds_runner --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'SDL runner build failed' }
Copy-Item -LiteralPath "$sdk/x86_64-w64-mingw32/bin/SDL3.dll" `
    -Destination "$repo/build/task-o-sdl-runner/SDL3.dll"
```

PATH changes above are session/process-local only. The runner CMake currently
has no SDL DLL post-build-copy rule, so adjacent DLL placement is explicit.
Check the built executable's import dependencies before smoke testing; keep any
necessary compiler-runtime resolution local to the launch rather than installing
machine-wide libraries. Existing toml++ and generated banks are reused; no
ROM-derived code regeneration/manual edits are involved.

The separate build directory does **not yet exist**. After a successful future
build, perform only the authorized ordinary-output window smoke/close test with
J/N custom selectors disabled, then stop O.5. No full Task O quiz proof or
frontend hold servicing is authorized here.

## Existing headless build preserved

One minimal loader/help check passed: `build/task-a-runner/nds_runner.exe --help`
returned **0**, printed usage including `--interactive`, with no ROM/save
supplied and no guest execution. The inline checker initially assumed help
would return 1; the recorded exit 0 was independently validated without a
repeat launch. That helper assertion is not a runner/frontend failure.

Before/after executable SHA-256:
`19ddb95320ccca985b42ead833c5add233a3d315222dff962c21fae1e022d76c`.
Before/after CMake cache SHA-256:
`6dae0ee28634f24cb79412184301d2ab63b12c94a929fed4ec231c39c2593446`.
Cache still records `NDS_SDL_BACKEND=NONE`.

Evidence: `local/task-o5/headless-check-001/{identity.json,stdout.log,stderr.log}`.
Prior A-O runtime captures and headless build were not overwritten. No game
window, title/class/handle, client size, guest-output capture or deterministic
window-close observation is available from O.5.

## Safety and execution posture

Only this ROM-free report is added. No SDL binaries/archives, local inventories,
ROM/save/state/screenshots or generated code are committed. `local/` and `build/`
remain ignored. No guest VRAM, save/progression, ROM, generated-C, custom quiz,
touch/presentation-owner or hold-loop modification. No exercise, Task O retry,
or Task P began.

Narrow supported escalations ran under existing auto-review without human
approval. No sandbox/network/full-access/relay policy changes. Official release
metadata/documentation was browsed to make the dependency request precise;
no SDK download, install, or network-fetch configure was attempted. No new
execution-infrastructure failure was observed.
