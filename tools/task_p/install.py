"""Install the owned title headers plus the existing generic runner facilities."""

import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    subprocess.run(["python", str(root / "tools/task_o/install.py"), "--codex-executable", str(args.codex_executable)], check=True)


if __name__ == "__main__":
    main()
