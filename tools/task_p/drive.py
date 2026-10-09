"""Use the stable host activation with the proven real-window SDL test driver."""

import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--disabled-control", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    command = ["python", str(root / "tools/task_o/drive_frontend.py"), "--out", str(args.out), "--brainage-host", "--input-source", "sdl-queue"]
    if args.disabled_control:
        command.append("--disabled-control")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
