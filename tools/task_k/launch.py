"""Restore the unchanged Training-menu checkpoint, explicitly selecting normal or forced execution."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument("--forced-regression", action="store_true")
    parser.add_argument("--ds-presentation", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = args.out.resolve()
    assert any(output.is_relative_to(root / name) for name in ("local/task-k", "local/task-l", "local/task-m", "local/task-n"))
    assert not args.ds_presentation or args.enabled
    environment = os.environ.copy()
    environment["NDS_TASK_J_CUSTOM_EXERCISE_PROBE"] = "1" if args.enabled else "0"
    environment["NDS_TASK_J_TRACE"] = str(output / "native-probe.jsonl")
    environment["NDS_TASK_J_CONTROL"] = str(output / "native-control.txt")
    environment["NDS_TASK_J_PANEL_CAPTURE"] = str(output / "native-panel.bmp")
    environment["NDS_TASK_K_TRACE"] = str(output / "entries.jsonl")
    environment["NDS_TASK_N_DS_PRESENTATION"] = "1" if args.ds_presentation else "0"
    environment["NDS_TASK_N_CAPTURE_ROOT"] = str(output)
    command = [sys.executable, str(root / "tools/task_i/restore_menu.py"),
               "--source", str(root / "local/task-g/session-001/04-training-menu"),
               "--out", str(output), "--port", str(args.port)]
    if not args.forced_regression:
        command.append("--normal")
    subprocess.run(command, env=environment, check=True)


if __name__ == "__main__":
    main()
