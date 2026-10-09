"""Apply the narrow Task J native proof to the pinned runner, without editing generated C."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    framework = root / "local/ndsrecomp"
    assert subprocess.check_output(["git", "-C", str(framework), "rev-parse", "HEAD"], text=True).strip() == "3a57236bb23d25dcb4caad7d58d733311062ff5e"
    header = (root / "tools/task_j/brainage_native_probe.h").read_text()
    destination = framework / "runner/src/brainage_native_probe.h"
    patches = []
    if destination.exists():
        assert destination.read_text() == header, "existing Task J header differs"
    else:
        patches.append("*** Add File: local/ndsrecomp/runner/src/brainage_native_probe.h\n" +
                       "\n".join("+" + line for line in header.splitlines()))
    edits = [
        ("runner/src/main.cpp", '#include "title_patches.h"', '#include "brainage_native_probe.h"'),
        ("runner/src/main.cpp", "    debug_set_savestate_identity(NDS_RUNNER_BUILD_ID, rom_sha1);",
         "    brainage_task_j::initialize(rom_sha1.c_str());"),
        ("runner/src/tier3.cpp", '#include "brainage_launch_trace.h"', '#include "brainage_native_probe.h"'),
        ("runner/src/tier3.cpp", "            if (condition_passed) task_i_snapshot(pc, thumb, in.raw, ic.R);",
         "            if (condition_passed) brainage_task_j::before_instruction(pc, thumb, in.raw, ic.R, pack_cpsr(ic));"),
        ("runner/CMakeLists.txt", "    target_link_libraries(nds_runner PRIVATE ws2_32)",
         "    target_link_libraries(nds_runner PRIVATE user32 gdi32)"),
    ]
    for filename, anchor, added in edits:
        contents = (framework / filename).read_text()
        if added in contents:
            continue
        assert contents.count(anchor) == 1, f"unexpected anchor in {filename}"
        patches.append(f"*** Update File: local/ndsrecomp/{filename}\n@@\n {anchor}\n+{added}")
    if patches:
        patch = "*** Begin Patch\n" + "\n".join(patches) + "\n*** End Patch\n"
        subprocess.run([str(args.codex_executable.resolve()), "--codex-run-as-apply-patch", patch], cwd=root, check=True)
    subprocess.run([sys.executable, str(root / "tools/task_k/install.py"),
                    "--codex-executable", str(args.codex_executable.resolve())], check=True)
    print("Shared Task J/K probe installed; rebuild nds_runner. Disabled unless NDS_TASK_J_CUSTOM_EXERCISE_PROBE=1")


if __name__ == "__main__":
    main()
