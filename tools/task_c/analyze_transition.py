"""Audit only the measured completion interval and its tracing positive control."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task_a"))
from route_marker import ranges


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory
    before_summary = json.loads((root / args.before / "summary.json").read_text())
    after_summary = json.loads((root / args.after / "summary.json").read_text())
    before = (root / args.before / "after.sav").read_bytes()
    after = (root / args.after / "after.sav").read_bytes()
    assert len(before) == len(after) == 262144
    assert before.find(b"CLEAR-RAM-CHECK") == after.find(b"CLEAR-RAM-CHECK") == 0x180
    flash = records(root / "flash.jsonl")
    requests = records(root / "requests.jsonl")
    ledger = bytearray((root / "initial.sav").read_bytes())
    for sequence, event in enumerate(flash, 1):
        assert event["sequence"] == sequence
        old, new = bytes.fromhex(event["old_hex"]), bytes.fromhex(event["new_hex"])
        assert len(old) == len(new) == event["length"]
        for index, value in enumerate(new):
            offset = (event["offset"] + index) & event["wrap_mask"]
            assert ledger[offset] == old[index]
            ledger[offset] = value
    assert bytes(ledger) == after
    assert [event["sequence"] for event in requests] == list(range(1, len(requests) + 1))
    start_cycle = before_summary["final"]["counts"]["cyc9"] // 2
    end_cycle = after_summary["final"]["counts"]["cyc9"] // 2
    measured_requests = [event for event in requests if start_cycle <= event["system_cycles"] <= end_cycle and event["kind"] == "submit"]
    measured_flash = [event for event in flash if start_cycle <= event["byte_origin"]["system_cycles"] <= end_cycle]
    reference_requests = records(args.reference / "requests.jsonl")
    marker = b"CLEAR-RAM-CHECK\0"
    submits = [event for event in reference_requests if event["kind"] == "submit" and event["offset"] == 0x180]
    assert len(submits) == 1
    submitted = submits[0]
    assert submitted["length"] == 16 and bytes.fromhex(submitted["payload_hex"]) == marker
    assert submitted["pc"] == "0x0200E080" and submitted["shared"] == 0x020d4ce0
    following = reference_requests[submitted["sequence"]:submitted["sequence"] + 3]
    assert [event["kind"] for event in following] == ["fifo_send", "fifo_receive", "arm7_write"]
    assert all(event["offset"] == 0x180 and event["length"] == 16 and bytes.fromhex(event["payload_hex"]) == marker for event in following)
    reference_flash = records(args.reference / "flash.jsonl")
    commits = [event for event in reference_flash if event["transaction"] == 1481]
    assert len(commits) == 16
    assert bytes.fromhex("".join(event["new_hex"] for event in commits)) == marker
    assert submitted["system_cycles"] < following[-1]["system_cycles"] < commits[0]["byte_origin"]["system_cycles"]
    count, spans = ranges(before, after)
    report = {"classification": "A" if not measured_requests and not measured_flash and not count else "F",
              "before_checkpoint": args.before, "after_checkpoint": args.after,
              "before_sha256": hashlib.sha256(before).hexdigest(),
              "after_sha256": hashlib.sha256(after).hexdigest(), "changed_bytes": count,
              "changed_ranges_half_open": spans, "system_cycle_interval": [start_cycle, end_cycle],
              "logical_requests": measured_requests, "flash_events": measured_flash,
              "total_requests_since_restore": len([event for event in requests if event["kind"] == "submit"]),
              "total_flash_events_since_restore": len(flash), "replay_matches_live_snapshot": True,
              "positive_control": {"submitted": submitted, "following": following,
                                   "flash_sequences": [event["sequence"] for event in commits]},
              "all_checkpoints_match_baseline": all((path / "after.sav").read_bytes() == before for path in root.iterdir() if path.is_dir() and (path / "summary.json").exists())}
    (root / "transition-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "positive_control"}, indent=2))


if __name__ == "__main__":
    main()
