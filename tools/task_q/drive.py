"""Two continuous strokes through the real SDL frontend, using stable catalog selection."""

import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    subprocess.run(["python", str(root / "tools/task_o/drive_frontend.py"), "--out", str(args.out),
                    "--brainage-host", "--freehand", "--input-source", "sdl-queue"], check=True)


if __name__ == "__main__":
    main()
