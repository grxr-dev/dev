"""Install the small compiled-instruction callback and shared title probe on the pinned runtime."""

import argparse
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
    source = (root / "tools/task_j/brainage_native_probe.h").read_text()
    destination = framework / "runner/src/brainage_native_probe.h"
    old = destination.read_text()
    if old != source:
        patches.append("*** Update File: local/ndsrecomp/runner/src/brainage_native_probe.h\n@@\n" +
                       "\n".join("-" + line for line in old.splitlines()) + "\n" +
                       "\n".join("+" + line for line in source.splitlines()))
    if "nds_set_compiled_instruction_hook" not in (framework / "runner/src/io.h").read_text():
        body = (root / "tools/task_k/compiled-hook.patch").read_text().splitlines()[1:-1]
        patches.append("\n".join(body))
    if patches:
        patch = "*** Begin Patch\n" + "\n".join(patches) + "\n*** End Patch\n"
        subprocess.run([str(args.codex_executable.resolve()), "--codex-run-as-apply-patch", patch], cwd=root, check=True)
    assert destination.read_text() == source
    print("Task K compiled callback installed; activation unchanged and opt-in")


if __name__ == "__main__":
    main()
