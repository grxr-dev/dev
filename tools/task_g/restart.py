"""Fresh-launch a completed Task G snapshot on the unchanged January-2 guest date."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_f"))
from launch_return import decoded_rtc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=19855)
    args = parser.parse_args()
    summary = json.loads((args.source / "summary.json").read_text())
    assert decoded_rtc(summary["rtc_after"]).date().isoformat() == "2024-01-02"
    assert summary["api_operations"] == summary["accepted_bytes"] == 0, "use the quiet completion checkpoint"
    environment = os.environ.copy()
    environment["NDS_TASK_F_RTC_PLUS_ONE_DAY"] = "1"
    launcher = Path(__file__).resolve().parents[1] / "task_e" / "launch_saved.py"
    subprocess.run([sys.executable, str(launcher), "--source", str(args.source), "--out", str(args.out),
                    "--port", str(args.port)], env=environment, check=True)


if __name__ == "__main__":
    main()
