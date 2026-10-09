"""Start a same-day or exactly +1-day return from the authoritative Task E save."""

import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_e"))
from launch_saved import main as launch_saved


def decoded_rtc(state):
    def decimal(value):
        return (value >> 4) * 10 + (value & 15)
    assert state["status1"] & 2, "expected the validated 24-hour mode"
    year, month, day, weekday, hour, minute, second = state["datetime"]
    return datetime(2000 + decimal(year), decimal(month), decimal(day),
                    decimal(hour & 63), decimal(minute), decimal(second))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--plus-one-day", action="store_true")
    parser.add_argument("--reference", type=Path, default=Path("local/task-f/source-rtc-check/rtc-evidence.json"))
    args = parser.parse_args()
    source_session = json.loads((args.source.parent / "session.json").read_text())
    assert "--rtc-host" not in source_session["command"], "host time must not enter this controlled experiment"
    source_summary = json.loads((args.source / "summary.json").read_text())
    assert source_summary["save_sha256_after"] == "fa9c6b3253574bac7d2969943ff29175022264e6cb1e190a2b963e1cd499c40a"
    reference = json.loads(args.reference.read_text())["default_before_patch"]
    os.environ.pop("NDS_TASK_F_RTC_PLUS_ONE_DAY", None)
    if args.plus_one_day:
        os.environ["NDS_TASK_F_RTC_PLUS_ONE_DAY"] = "1"
    sys.argv = ["launch_saved", "--source", str(args.source), "--out", str(args.out), "--port", str(args.port)]
    launch_saved()
    with socket.create_connection(("127.0.0.1", args.port), timeout=120) as connection:
        wire = connection.makefile("rwb")
        wire.write(json.dumps({"cmd": "rtc_state"}).encode() + b"\n")
        wire.flush()
        rtc = json.loads(wire.readline())
    expected = decoded_rtc(reference) + timedelta(days=int(args.plus_one_day))
    assert decoded_rtc(rtc) == expected
    assert rtc["datetime"][3] == (reference["datetime"][3] + int(args.plus_one_day)) % 7
    assert rtc["datetime"][4:] == reference["datetime"][4:]
    assert rtc["status1"] == reference["status1"] and rtc["status2"] == reference["status2"]
    if not args.plus_one_day:
        assert rtc == reference, "disabled RTC behavior changed"
    report = {"plus_one_day": args.plus_one_day, "rtc": rtc, "decoded": decoded_rtc(rtc).isoformat(),
              "reference": reference, "difference_seconds": int((decoded_rtc(rtc) - decoded_rtc(reference)).total_seconds()),
              "host_clock_used": False, "host_clock_changed": False}
    (args.out / "rtc-control.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
