"""Install the small compiled-instruction callback and shared title probe on the pinned runtime."""

import argparse
import difflib
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    framework = root / "local/ndsrecomp"
    assert subprocess.check_output(["git", "-C", str(framework), "rev-parse", "HEAD"], text=True).strip() == "3a57236bb23d25dcb4caad7d58d733311062ff5e"
    patches = []
    headers = (("tools/task_j/brainage_native_probe.h", "brainage_native_probe.h"),
               ("tools/task_l/mini_exercise_state.h", "mini_exercise_state.h"),
               ("tools/task_m/touch_state.h", "touch_state.h"),
               ("tools/task_n/native_surface.h", "native_surface.h"))
    for filename, name in headers:
        source = (root / filename).read_text()
        destination = framework / "runner/src" / name
        if not destination.exists():
            patches.append(f"*** Add File: local/ndsrecomp/runner/src/{name}\n" +
                           "\n".join("+" + line for line in source.splitlines()))
        elif destination.read_text() != source:
            old = destination.read_text()
            changes = list(difflib.unified_diff(old.splitlines(), source.splitlines(), n=3))[2:]
            patches.append(f"*** Update File: local/ndsrecomp/runner/src/{name}\n" +
                           "\n".join("@@" if line.startswith("@@") else line for line in changes))
    if "nds_set_compiled_instruction_hook" not in (framework / "runner/src/io.h").read_text():
        body = (root / "tools/task_k/compiled-hook.patch").read_text().splitlines()[1:-1]
        patches.append("\n".join(body))
    if "nds_set_touch_owner" not in (framework / "runner/src/io.h").read_text():
        patches.append("\n".join((root / "tools/task_m/touch-owner.patch").read_text().splitlines()[1:-1]))
    if 'cmd == "touch_state"' not in (framework / "runner/src/debug_server.cpp").read_text():
        patches.append("\n".join((root / "tools/task_m/touch-debug.patch").read_text().splitlines()[1:-1]))
    if "nds_gpu2d_set_bottom_presentation" not in (framework / "runner/src/gpu2d.h").read_text():
        patches.append("\n".join((root / "tools/task_n/presentation.patch").read_text().splitlines()[1:-1]))
    if patches:
        patch = "*** Begin Patch\n" + "\n".join(patches) + "\n*** End Patch\n"
        subprocess.run([str(args.codex_executable.resolve()), "--codex-run-as-apply-patch", patch], cwd=root, check=True)
    for filename, name in headers:
        assert (framework / "runner/src" / name).read_text() == (root / filename).read_text()
    print("Task K compiled callback installed; activation unchanged and opt-in")


if __name__ == "__main__":
    main()
