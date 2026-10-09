"""Audit one Task G session and its separate same-date persistence restart."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_e"))
from analyze_save import audit, digest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_f"))
from launch_return import decoded_rtc


def phases(root):
    session = json.loads((root / "session.json").read_text())
    result, requests, commits = [], 0, 0
    for label in session["checkpoints"]:
        summary = json.loads((root / label / "summary.json").read_text())
        date = decoded_rtc(summary["rtc_after"])
        assert date.date().isoformat() == "2024-01-02"
        events = [json.loads(line) for line in (root / label / "requests.jsonl").read_text().splitlines()]
        operations = [event for event in events if event["kind"] == "write_api"]
        assert len(operations) == summary["api_operations"]
        result.append({"label": label, "tap": summary["tap"], "answer": summary.get("answer"),
                       "system_before": summary["initial"]["counts"]["cyc7"],
                       "system_after": summary["final"]["counts"]["cyc7"],
                       "rtc_after": date.isoformat(), "api_count_before": requests,
                       "api_count_after": requests + len(operations), "api_operations": len(operations),
                       "commits_before": commits, "commits_after": commits + summary["accepted_bytes"],
                       "accepted_bytes": summary["accepted_bytes"], "changed_bytes": summary["changed_bytes"],
                       "before_sha256": summary["save_sha256_before"],
                       "after_sha256": summary["save_sha256_after"],
                       "api_sequences": [event["sequence"] for event in operations]})
        requests += len(operations)
        commits += summary["accepted_bytes"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--completed", default="51-completed-quiet")
    parser.add_argument("--restart", type=Path, required=True)
    parser.add_argument("--restart-checkpoint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.session, args.completed)
    result["phases"] = phases(args.session)
    assert result["initial_sha256"] == "a105aaff6472a7ab86132c69c7df94b9490fbfa04aca19e50855abda87bf1abb"
    baseline = (args.session / "initial.sav").read_bytes()
    completed = (args.session / args.completed / "after.sav").read_bytes()
    result["changed_hex"] = [{"start": start, "end_inclusive": end,
                              "before": baseline[start:end + 1].hex(), "after": completed[start:end + 1].hex()}
                             for start, end in result["changed_ranges_inclusive"]]
    result["exercise_record_mirror_equal"] = completed[0x1b20:0x1b40] == completed[0x21b20:0x21b40]
    reloaded = json.loads((args.restart / "reload.json").read_text())
    assert reloaded["exact_image_loaded"] and not reloaded["savestate_imported"]
    assert reloaded["reload_sha256"] == result["final_sha256"]
    result["restart"] = audit(args.restart, args.restart_checkpoint)
    result["restart"]["phases"] = phases(args.restart)
    result["restart"]["exact_completed_image_loaded"] = True
    assert result["restart"]["initial_sha256"] == result["final_sha256"]
    disk = (args.restart / "erased.sav").read_bytes()
    assert digest(disk) == result["restart"]["final_sha256"]
    for operation in result["operations"]:
        start = operation["offset"]
        end = start + operation["length"]
        assert disk[start:end] == completed[start:end]
    result["restart"]["exercise_and_stamp_written_ranges_preserved"] = True
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("initial_sha256", "final_sha256", "api_operation_count",
                                                    "submission_count", "accepted_bytes", "changed_byte_commits",
                                                    "net_changed_bytes", "quiet_system_cycles")}, indent=2))
    print("restart operations:", result["restart"]["api_operation_count"])


if __name__ == "__main__":
    main()
