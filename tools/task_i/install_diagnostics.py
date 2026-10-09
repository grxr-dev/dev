"""Install the opt-in Task I call observer through apply_patch on the pinned runner."""

import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    framework = root / "local/ndsrecomp"
    commit = subprocess.check_output(
        ["git", "-C", str(framework), "rev-parse", "HEAD"], text=True
    ).strip()
    assert commit == "3a57236bb23d25dcb4caad7d58d733311062ff5e"
    source = framework / "runner/src/tier3.cpp"
    contents = source.read_text()
    assert "task_c_snapshot(pc, thumb, ic.R);" in contents
    assert "TaskAInstructionScope task_a_instruction_scope(pc, thumb);" in contents
    header = (root / "tools/task_i/brainage_launch_trace.h").read_text()
    destination = framework / "runner/src/brainage_launch_trace.h"
    patches = []
    if destination.exists():
        assert destination.read_text() == header, "existing Task I header differs"
    else:
        patches.append("*** Add File: local/ndsrecomp/runner/src/brainage_launch_trace.h\n" +
                       "\n".join("+" + line for line in header.splitlines()))
    include = '#include "brainage_launch_trace.h"'
    if include not in contents:
        anchor = '#include "brainage_task_c_trace.h"'
        assert contents.count(anchor) == 1
        patches.append("*** Update File: local/ndsrecomp/runner/src/tier3.cpp\n@@\n " +
                       anchor + "\n+" + include)
    hook = "if (condition_passed) task_i_snapshot(pc, thumb, in.raw, ic.R);"
    if hook not in contents:
        anchor = "            task_c_snapshot(pc, thumb, ic.R);"
        assert contents.count(anchor) == 1
        patches.append("*** Update File: local/ndsrecomp/runner/src/tier3.cpp\n@@\n " +
                       anchor + "\n+            " + hook)
    if patches:
        patch = "*** Begin Patch\n" + "\n".join(patches) + "\n*** End Patch\n"
        subprocess.run([str(args.codex_executable.resolve()), "--codex-run-as-apply-patch", patch],
                       cwd=root, check=True)
    print("Task I observer installed; rebuild nds_runner and set NDS_TASK_I_TRACE with --force-tier3")


if __name__ == "__main__":
    main()
