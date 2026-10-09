"""Build an isolated SDL3 runner from the locally supplied, pinned MinGW SDK."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile


ARCHIVE_SHA256 = "cd98158c8d025a816f430a600b4e9526524e6219ee884ec72bd498b80fd3bf58"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    root = args.out.resolve()
    if not root.is_relative_to(repository / "local/task-o5"):
        raise ValueError("evidence must be under local/task-o5")
    root.mkdir(parents=True, exist_ok=False)
    toolchain = repository / "local/toolchain"
    archive = toolchain / "SDL3-devel-3.4.18-mingw.zip"
    if digest(archive) != ARCHIVE_SHA256:
        raise ValueError("SDL archive identity mismatch")
    sdk = toolchain / "SDL3-3.4.18"
    if not sdk.exists():
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                target = (toolchain / member.filename).resolve()
                if not target.is_relative_to(sdk):
                    raise ValueError("unexpected SDK archive path")
            package.extractall(toolchain)
    prefix = sdk / "x86_64-w64-mingw32"
    for relative in ("include/SDL3/SDL.h", "lib/libSDL3.dll.a", "bin/SDL3.dll", "lib/cmake/SDL3/SDL3Config.cmake"):
        if not (prefix / relative).is_file():
            raise ValueError(f"missing SDL development material: {relative}")
    headless = repository / "build/task-a-runner"
    protected = [headless / "nds_runner.exe", headless / "CMakeCache.txt"]
    for folder in (repository / "generated/public", repository / "generated/brainage"):
        protected.extend(sorted(path for path in folder.glob("*") if path.suffix in (".c", ".h")))
    before = {str(path.relative_to(repository)): digest(path) for path in protected}
    (root / "protected-before.json").write_text(json.dumps(before, indent=2) + "\n")
    binary = toolchain / "w64devkit/bin"
    build = repository / "build/task-o-sdl-runner"
    command = [
        str(binary / "cmake.exe"), "-S", str(repository / "local/ndsrecomp/runner"),
        "-B", str(build), "-G", "Ninja",
        f"-DCMAKE_MAKE_PROGRAM={binary / 'ninja.exe'}",
        f"-DCMAKE_C_COMPILER={binary / 'gcc.exe'}", f"-DCMAKE_CXX_COMPILER={binary / 'g++.exe'}",
        "-DCMAKE_BUILD_TYPE=Release", "-DNDS_SDL_BACKEND=SDL3",
        f"-DSDL3_DIR={prefix / 'lib/cmake/SDL3'}", f"-DCMAKE_PREFIX_PATH={prefix}",
        "-DNDS_ENABLE_COMPUTE_RENDERER=OFF", "-DNDS_BOOTSTRAP_FIRMWARE=ON",
        f"-DNDS_GENERATED_DIR={repository / 'generated/public'}",
        f"-DNDS_TITLE_BANK_DIR={repository / 'generated/brainage'}",
        "-DNDS_TITLE_ROM_SHA1=b8a105bacc3234dede8d4465df0869f2b922a0e2",
        f"-DNDS_RECOMP_UI_ROOT={repository / 'local/recomp-ui'}",
        f"-DNDSRECOMP_TOMLPP_HEADER={repository / 'local/ndsrecomp/recompiler/third_party/toml.hpp'}",
        "-DNDSRECOMP_COMPILER_CACHE=OFF", "-DNDSRECOMP_COMPILE_JOBS=4", "-DNDSRECOMP_LINK_JOBS=1",
    ]
    build_command = [str(binary / "cmake.exe"), "--build", str(build), "--target", "nds_runner", "--parallel", "4"]
    environment = os.environ.copy()
    environment["PATH"] = str(binary) + os.pathsep + environment.get("PATH", "")
    evidence = {"archive_sha256": ARCHIVE_SHA256, "sdk_prefix": str(prefix),
                "configure_command": command, "build_command": build_command}
    (root / "commands.json").write_text(json.dumps(evidence, indent=2) + "\n")
    for label, arguments in (("configure", command), ("build", build_command)):
        print(f"{label}: starting", flush=True)
        with (root / f"{label}.log").open("wb") as output:
            result = subprocess.run(arguments, cwd=repository, env=environment, stdout=output, stderr=subprocess.STDOUT)
        evidence[f"{label}_exit_code"] = result.returncode
        print(f"{label}: exit {result.returncode}; log {root / (label + '.log')}", flush=True)
        if result.returncode:
            break
    after = {str(path.relative_to(repository)): digest(path) for path in protected}
    evidence["protected_inputs_unchanged"] = before == after
    evidence["protected_file_count"] = len(protected)
    (root / "protected-after.json").write_text(json.dumps(after, indent=2) + "\n")
    if evidence.get("build_exit_code") == 0:
        shutil.copy2(prefix / "bin/SDL3.dll", build / "SDL3.dll")
        evidence["runner_sha256"] = digest(build / "nds_runner.exe")
        evidence["sdl_dll_sha256"] = digest(build / "SDL3.dll")
    (root / "build-result.json").write_text(json.dumps(evidence, indent=2) + "\n")
    if not evidence["protected_inputs_unchanged"]:
        raise RuntimeError("protected headless/generated inputs changed")
    if evidence.get("build_exit_code") != 0:
        raise RuntimeError("SDL runner did not build; see preserved configure/build logs")
    print(json.dumps(evidence, indent=2), flush=True)


if __name__ == "__main__":
    main()
