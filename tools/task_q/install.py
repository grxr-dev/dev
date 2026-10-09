"""Install owned exercise headers and the bounded frontend motion diagnostic extension."""

import argparse
import difflib
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    subprocess.run(["python", str(root / "tools/task_p/install.py"), "--codex-executable", str(args.codex_executable)], check=True)
    path = root / "local/ndsrecomp/runner/src/frontend.cpp"
    for begin, end, owned in (("void task_o_queue_frontend_button(", "uint64_t task_o_input_sequence = 0;", "queue_input.inc"),
                              ("uint64_t task_o_input_sequence = 0;", "void set_touch_from_mouse(", "event_trace.inc")):
        old = path.read_text()
        assert old.count(begin) == old.count(end) == 1
        start, finish = old.index(begin), old.index(end)
        new = old[:start] + (root / "tools/task_o" / owned).read_text().rstrip() + "\n\n" + old[finish:]
        if old == new:
            continue
        changes = list(difflib.unified_diff(old.splitlines(), new.splitlines(), n=3))[2:]
        patch = "*** Begin Patch\n*** Update File: local/ndsrecomp/runner/src/frontend.cpp\n" + "\n".join("@@" if line.startswith("@@") else line for line in changes) + "\n*** End Patch\n"
        subprocess.run([str(args.codex_executable.resolve()), "--codex-run-as-apply-patch", patch], cwd=root, check=True)
    print("Task Q owned headers/motion diagnostics installed; host and hold service unchanged")


if __name__ == "__main__":
    main()
